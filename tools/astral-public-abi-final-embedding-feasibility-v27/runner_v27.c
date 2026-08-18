/*
 * V27 public-ABI final-embedding feasibility runner.
 *
 * State slice: astral-public-abi-final-embedding-feasibility-v27-execution.
 * The runner emits aggregate metrics only. It does not write prompts, raw
 * embeddings, raw logits, control vectors, or model output.
 */

#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "llama.h"

#define PROTOCOL "astral-public-abi-final-embedding-feasibility-v27"
#define EMBEDDING_TOLERANCE 1e-4f
#define EFFECT_GATE 1e-4f
#define CONTROL_LAYER 1
#define CONTROL_AMPLITUDE 1.0f

typedef struct {
    float * embedding;
    float logit_a;
    float logit_b;
    int32_t embedding_dim;
} Observation;

static void fail(const char * code) {
    fprintf(stderr, "V27_STOP:%s\n", code);
    _Exit(2);
}

static int32_t tokenize_one(const struct llama_vocab * vocab, const char * text) {
    int32_t required = llama_tokenize(vocab, text, (int32_t) strlen(text), NULL, 0, false, false);
    if (required < 0) {
        required = -required;
    }
    if (required <= 0 || required > 16) {
        fail("TokenNotSingle");
    }
    llama_token * tokens = (llama_token *) calloc((size_t) required, sizeof(llama_token));
    if (tokens == NULL) {
        fail("Allocation");
    }
    int32_t count = llama_tokenize(vocab, text, (int32_t) strlen(text), tokens, required, false, false);
    if (count != 1) {
        free(tokens);
        fail("TokenNotSingle");
    }
    int32_t token = tokens[0];
    free(tokens);
    return token;
}

static int32_t tokenize_prompt(const struct llama_vocab * vocab, const char * prompt, llama_token ** output) {
    int32_t needed = llama_tokenize(vocab, prompt, (int32_t) strlen(prompt), NULL, 0, true, false);
    if (needed < 0) {
        needed = -needed;
    }
    if (needed <= 0 || needed > 2048) {
        fail("PromptTokenizationSize");
    }
    llama_token * tokens = (llama_token *) calloc((size_t) needed, sizeof(llama_token));
    if (tokens == NULL) {
        fail("Allocation");
    }
    int32_t count = llama_tokenize(vocab, prompt, (int32_t) strlen(prompt), tokens, needed, true, false);
    if (count != needed) {
        free(tokens);
        fail("PromptTokenizationMismatch");
    }
    *output = tokens;
    return count;
}

static Observation observe(
    struct llama_model * model,
    const llama_token * tokens,
    int32_t token_count,
    int32_t token_a,
    int32_t token_b,
    const float * control,
    int32_t embedding_dim,
    int32_t layer_count
) {
    struct llama_context_params context_params = llama_context_default_params();
    context_params.n_ctx = 512;
    context_params.n_batch = 512;
    context_params.n_ubatch = 512;
    /* Embedding mode may materialize one output per prompt token. */
    context_params.n_outputs_max = (uint32_t) token_count;
    context_params.embeddings = true;
    context_params.n_threads = 4;
    context_params.n_threads_batch = 4;

    struct llama_context * context = llama_init_from_model(model, context_params);
    if (context == NULL) {
        fail("ContextInit");
    }

    float * control_storage = NULL;
    if (control != NULL) {
        control_storage = (float *) calloc((size_t) embedding_dim, sizeof(float));
        if (control_storage == NULL) {
            llama_free(context);
            fail("Allocation");
        }
        memcpy(control_storage, control, (size_t) embedding_dim * sizeof(float));
        int32_t control_status = llama_set_adapter_cvec(
            context, control_storage, (size_t) embedding_dim, embedding_dim,
            CONTROL_LAYER, CONTROL_LAYER
        );
        if (control_status != 0) {
            free(control_storage);
            llama_free(context);
            fail("ControlVectorSet");
        }
    }

    struct llama_batch batch = llama_batch_init(token_count, 0, 1);
    if (batch.token == NULL || batch.pos == NULL || batch.n_seq_id == NULL || batch.seq_id == NULL || batch.logits == NULL) {
        free(control_storage);
        llama_free(context);
        fail("BatchInit");
    }
    /* llama_batch_init allocates capacity; the active count starts at zero. */
    batch.n_tokens = token_count;
    for (int32_t i = 0; i < token_count; i++) {
        batch.token[i] = tokens[i];
        batch.pos[i] = i;
        batch.n_seq_id[i] = 1;
        batch.seq_id[i][0] = 0;
        batch.logits[i] = (i == token_count - 1) ? 1 : 0;
    }
    int32_t decode_status = llama_decode(context, batch);
    if (decode_status != 0) {
        llama_batch_free(batch);
        free(control_storage);
        llama_free(context);
        fail("Decode");
    }
    float * embedding = llama_get_embeddings_ith(context, -1);
    float * logits = llama_get_logits_ith(context, -1);
    if (embedding == NULL || logits == NULL) {
        llama_batch_free(batch);
        free(control_storage);
        llama_free(context);
        fail("OutputUnavailable");
    }

    Observation observation = {0};
    observation.embedding_dim = embedding_dim;
    observation.embedding = (float *) calloc((size_t) embedding_dim, sizeof(float));
    if (observation.embedding == NULL) {
        llama_batch_free(batch);
        free(control_storage);
        llama_free(context);
        fail("Allocation");
    }
    observation.logit_a = logits[token_a];
    observation.logit_b = logits[token_b];
    for (int32_t i = 0; i < embedding_dim; i++) {
        observation.embedding[i] = embedding[i];
    }

    llama_batch_free(batch);
    free(control_storage);
    llama_free(context);
    (void) layer_count;
    return observation;
}

static bool finite_observation(const Observation * observation) {
    if (!isfinite(observation->logit_a) || !isfinite(observation->logit_b)) {
        return false;
    }
    for (int32_t i = 0; i < observation->embedding_dim; i++) {
        if (!isfinite(observation->embedding[i])) {
            return false;
        }
    }
    return true;
}

static float max_abs_diff(const Observation * left, const Observation * right) {
    float maximum = 0.0f;
    for (int32_t i = 0; i < left->embedding_dim; i++) {
        float difference = fabsf(left->embedding[i] - right->embedding[i]);
        if (difference > maximum) {
            maximum = difference;
        }
    }
    maximum = fmaxf(maximum, fabsf(left->logit_a - right->logit_a));
    maximum = fmaxf(maximum, fabsf(left->logit_b - right->logit_b));
    return maximum;
}

static float embedding_norm(const Observation * observation) {
    double sum = 0.0;
    for (int32_t i = 0; i < observation->embedding_dim; i++) {
        sum += (double) observation->embedding[i] * (double) observation->embedding[i];
    }
    return (float) sqrt(sum);
}

static void free_observation(Observation * observation) {
    free(observation->embedding);
    observation->embedding = NULL;
}

int main(int argc, char ** argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: runner_v27 <model.gguf> <prompt>\n");
        return 2;
    }
    const char * model_path = argv[1];
    const char * prompt = argv[2];

    llama_backend_init();
    struct llama_model_params model_params = llama_model_default_params();
    model_params.n_gpu_layers = -1;
    struct llama_model * model = llama_model_load_from_file(model_path, model_params);
    if (model == NULL) {
        llama_backend_free();
        fail("ModelLoad");
    }
    const struct llama_vocab * vocab = llama_model_get_vocab(model);
    if (vocab == NULL) {
        llama_model_free(model);
        llama_backend_free();
        fail("VocabularyUnavailable");
    }
    int32_t embedding_dim = llama_model_n_embd(model);
    int32_t layer_count = llama_model_n_layer(model);
    if (embedding_dim <= 0 || layer_count <= CONTROL_LAYER) {
        llama_model_free(model);
        llama_backend_free();
        fail("ModelDimensions");
    }
    llama_token * tokens = NULL;
    int32_t token_count = tokenize_prompt(vocab, prompt, &tokens);
    int32_t token_a = tokenize_one(vocab, " A");
    int32_t token_b = tokenize_one(vocab, " B");

    float * zero = (float *) calloc((size_t) embedding_dim, sizeof(float));
    float * nonzero = (float *) calloc((size_t) embedding_dim, sizeof(float));
    if (zero == NULL || nonzero == NULL) {
        free(zero);
        free(nonzero);
        free(tokens);
        llama_model_free(model);
        llama_backend_free();
        fail("Allocation");
    }
    nonzero[0] = CONTROL_AMPLITUDE;

    Observation clean = observe(model, tokens, token_count, token_a, token_b, NULL, embedding_dim, layer_count);
    Observation zero_observation = observe(model, tokens, token_count, token_a, token_b, zero, embedding_dim, layer_count);
    Observation clean_repeat = observe(model, tokens, token_count, token_a, token_b, NULL, embedding_dim, layer_count);
    Observation intervention = observe(model, tokens, token_count, token_a, token_b, nonzero, embedding_dim, layer_count);
    Observation intervention_repeat = observe(model, tokens, token_count, token_a, token_b, nonzero, embedding_dim, layer_count);

    bool finite = finite_observation(&clean) && finite_observation(&zero_observation)
        && finite_observation(&clean_repeat) && finite_observation(&intervention)
        && finite_observation(&intervention_repeat);
    float clean_zero_error = max_abs_diff(&clean, &zero_observation);
    float clean_repeat_error = max_abs_diff(&clean, &clean_repeat);
    float intervention_repeat_error = max_abs_diff(&intervention, &intervention_repeat);
    float clean_margin = clean.logit_a - clean.logit_b;
    float intervention_margin = intervention.logit_a - intervention.logit_b;
    float effect = fabsf(intervention_margin - clean_margin);
    bool parity = clean_zero_error <= EMBEDDING_TOLERANCE && clean_repeat_error <= EMBEDDING_TOLERANCE;
    bool repeatable = intervention_repeat_error <= EMBEDDING_TOLERANCE;
    bool effect_gate = effect >= EFFECT_GATE;
    const char * classification = (finite && parity && repeatable && effect_gate)
        ? "PublicAbiFinalEmbeddingInterventionFeasible"
        : "PublicAbiFinalEmbeddingInterventionStop";

    printf(
        "{\"protocol\":\"%s\",\"classification\":\"%s\",\"claim_ceiling\":\"LocalDevelopmentPublicAbiFinalEmbeddingFeasibility\",\"embedding_dim\":%d,\"layer_count\":%d,\"prompt_token_count\":%d,\"token_a\":%d,\"token_b\":%d,\"finite\":%s,\"clean_zero_max_abs_error\":%.9g,\"clean_repeat_max_abs_error\":%.9g,\"intervention_repeat_max_abs_error\":%.9g,\"clean_embedding_norm\":%.9g,\"intervention_embedding_norm\":%.9g,\"direct_logit_effect\":%.9g,\"parity_gate\":%s,\"repeatability_gate\":%s,\"effect_gate\":%s,\"model_execution\":true,\"network_access\":false}\n",
        PROTOCOL, classification, embedding_dim, layer_count, token_count,
        token_a, token_b, finite ? "true" : "false", clean_zero_error,
        clean_repeat_error, intervention_repeat_error, embedding_norm(&clean),
        embedding_norm(&intervention), effect, parity ? "true" : "false",
        repeatable ? "true" : "false", effect_gate ? "true" : "false"
    );

    free_observation(&clean);
    free_observation(&zero_observation);
    free_observation(&clean_repeat);
    free_observation(&intervention);
    free_observation(&intervention_repeat);
    free(zero);
    free(nonzero);
    free(tokens);
    llama_model_free(model);
    llama_backend_free();
    return (finite && parity && repeatable && effect_gate) ? 0 : 3;
}
