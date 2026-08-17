/*
 * V28 opaque causal-channel separation runner.
 *
 * State slice: astral-opaque-causal-channel-separation-v28-execution.
 * The runner streams derived trial summaries only. It never writes raw
 * embeddings, logits, prompts, control vectors, or model output.
 */

#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "llama.h"

#define PROTOCOL "astral-opaque-causal-channel-separation-v28"
#define FULL_FEATURES 16
#define OPAQUE_FEATURES 4
#define CONTROL_LAYER 1
#define CONTROL_COORDINATE 0
#define CONTROL_AMPLITUDE 0.5f
#define OPAQUE_QUANTIZATION 32.0f

typedef struct {
    float * embedding;
    float margin;
    int32_t embedding_dim;
} Observation;

static const char * const PROMPTS[] = {
    "Select the stable symbol. Answer: A or B.",
    "Choose the lower-risk branch. Answer: A or B.",
    "Pick the consistent label. Answer: A or B.",
    "Select the reversible option. Answer: A or B.",
    "Choose the bounded response. Answer: A or B.",
    "Pick the conservative path. Answer: A or B.",
    "Select the testable claim. Answer: A or B.",
    "Choose the auditable result. Answer: A or B.",
    "Pick the isolated case. Answer: A or B.",
    "Select the explicit boundary. Answer: A or B.",
    "Choose the fresh sample. Answer: A or B.",
    "Pick the held-out answer. Answer: A or B.",
    "Select the typed value. Answer: A or B.",
    "Choose the ordered block. Answer: A or B.",
    "Pick the valid context. Answer: A or B.",
    "Select the local result. Answer: A or B.",
};

static const size_t PROMPT_COUNT = sizeof(PROMPTS) / sizeof(PROMPTS[0]);

static void fail(const char * code) {
    fprintf(stderr, "V28_STOP:%s\n", code);
    _Exit(2);
}

static int32_t tokenize_one(const struct llama_vocab * vocab, const char * text) {
    int32_t required = llama_tokenize(vocab, text, (int32_t) strlen(text), NULL, 0, false, false);
    if (required < 0) {
        required = -required;
    }
    if (required != 1) {
        fail("TokenNotSingle");
    }
    llama_token * tokens = (llama_token *) calloc(1, sizeof(llama_token));
    if (tokens == NULL) {
        fail("Allocation");
    }
    int32_t count = llama_tokenize(vocab, text, (int32_t) strlen(text), tokens, 1, false, false);
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
    int32_t embedding_dim
) {
    struct llama_context_params context_params = llama_context_default_params();
    context_params.n_ctx = 512;
    context_params.n_batch = 512;
    context_params.n_ubatch = 512;
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
        int32_t status = llama_set_adapter_cvec(
            context, control_storage, (size_t) embedding_dim, embedding_dim,
            CONTROL_LAYER, CONTROL_LAYER
        );
        if (status != 0) {
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
    batch.n_tokens = token_count;
    for (int32_t i = 0; i < token_count; i++) {
        batch.token[i] = tokens[i];
        batch.pos[i] = i;
        batch.n_seq_id[i] = 1;
        batch.seq_id[i][0] = 0;
        batch.logits[i] = (i == token_count - 1) ? 1 : 0;
    }
    if (llama_decode(context, batch) != 0) {
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
    Observation result = {0};
    result.embedding_dim = embedding_dim;
    result.embedding = (float *) calloc((size_t) embedding_dim, sizeof(float));
    if (result.embedding == NULL) {
        llama_batch_free(batch);
        free(control_storage);
        llama_free(context);
        fail("Allocation");
    }
    result.margin = logits[token_a] - logits[token_b];
    for (int32_t i = 0; i < embedding_dim; i++) {
        result.embedding[i] = embedding[i];
    }
    llama_batch_free(batch);
    free(control_storage);
    llama_free(context);
    return result;
}

static bool finite_observation(const Observation * observation) {
    if (!isfinite(observation->margin)) {
        return false;
    }
    for (int32_t i = 0; i < observation->embedding_dim; i++) {
        if (!isfinite(observation->embedding[i])) {
            return false;
        }
    }
    return true;
}

static void free_observation(Observation * observation) {
    free(observation->embedding);
    observation->embedding = NULL;
}

static float sign_for(size_t feature, int32_t coordinate) {
    uint32_t value = (uint32_t) (feature + 1) * 2654435761u;
    value ^= (uint32_t) (coordinate + 17) * 2246822519u;
    value ^= value >> 13;
    return (value & 1u) == 0u ? -1.0f : 1.0f;
}

static void emit_trial(
    size_t trial,
    size_t split,
    const Observation * clean,
    const Observation * intervention
) {
    float delta[FULL_FEATURES];
    for (size_t feature = 0; feature < FULL_FEATURES; feature++) {
        double sum = 0.0;
        for (int32_t coordinate = 0; coordinate < clean->embedding_dim; coordinate++) {
            sum += (double) sign_for(feature, coordinate)
                * (double) (intervention->embedding[coordinate] - clean->embedding[coordinate]);
        }
        delta[feature] = (float) (sum / sqrt((double) clean->embedding_dim));
    }
    printf("{\"trial\":%zu,\"split\":%zu,\"target\":%.9g,\"full\":[", trial, split,
        intervention->margin - clean->margin);
    for (size_t feature = 0; feature < FULL_FEATURES; feature++) {
        if (feature != 0) {
            putchar(',');
        }
        printf("%.9g", delta[feature]);
    }
    printf("],\"opaque\":[");
    for (size_t feature = 0; feature < OPAQUE_FEATURES; feature++) {
        if (feature != 0) {
            putchar(',');
        }
        float quantized = roundf(delta[feature] * OPAQUE_QUANTIZATION) / OPAQUE_QUANTIZATION;
        printf("%.9g", quantized);
    }
    printf("],\"finite\":true}\n");
    fflush(stdout);
}

int main(int argc, char ** argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: runner_v28 <model.gguf>\n");
        return 2;
    }
    const char * model_path = argv[1];
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
    if (embedding_dim <= CONTROL_COORDINATE || layer_count <= CONTROL_LAYER) {
        llama_model_free(model);
        llama_backend_free();
        fail("ModelDimensions");
    }
    int32_t token_a = tokenize_one(vocab, " A");
    int32_t token_b = tokenize_one(vocab, " B");
    float * control = (float *) calloc((size_t) embedding_dim, sizeof(float));
    if (control == NULL) {
        llama_model_free(model);
        llama_backend_free();
        fail("Allocation");
    }
    control[CONTROL_COORDINATE] = CONTROL_AMPLITUDE;

    for (size_t trial = 0; trial < PROMPT_COUNT; trial++) {
        llama_token * tokens = NULL;
        int32_t token_count = tokenize_prompt(vocab, PROMPTS[trial], &tokens);
        Observation clean = observe(model, tokens, token_count, token_a, token_b, NULL, embedding_dim);
        Observation intervention = observe(model, tokens, token_count, token_a, token_b, control, embedding_dim);
        if (!finite_observation(&clean) || !finite_observation(&intervention)) {
            free_observation(&clean);
            free_observation(&intervention);
            free(tokens);
            free(control);
            llama_model_free(model);
            llama_backend_free();
            fail("NonFiniteObservation");
        }
        size_t split = trial < 8 ? 0 : (trial < 12 ? 1 : 2);
        emit_trial(trial, split, &clean, &intervention);
        free_observation(&clean);
        free_observation(&intervention);
        free(tokens);
    }
    free(control);
    llama_model_free(model);
    llama_backend_free();
    return 0;
}
