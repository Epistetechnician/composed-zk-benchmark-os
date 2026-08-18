/*
 * V29 calibrated opaque causal-channel runner.
 * State slice: astral-calibrated-opaque-causal-channel-v29-execution.
 * Only derived trial summaries are streamed; raw embeddings, logits, prompts,
 * controls, and model output are never written.
 */
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "llama.h"

#define FULL_FEATURES 4
#define OPAQUE_FEATURES 2
#define CONTROL_LAYER 1
#define CONTROL_COORDINATE 0
#define CONTROL_AMPLITUDE 0.75f
#define OPAQUE_QUANTIZATION 16.0f

typedef struct { float *embedding; float margin; int32_t dimension; } Observation;

static const char * const PROMPTS[] = {
    "Select the stable symbol for case 01. Answer: A or B.", "Select the stable symbol for case 02. Answer: A or B.",
    "Select the stable symbol for case 03. Answer: A or B.", "Select the stable symbol for case 04. Answer: A or B.",
    "Select the bounded branch for case 05. Answer: A or B.", "Select the bounded branch for case 06. Answer: A or B.",
    "Select the bounded branch for case 07. Answer: A or B.", "Select the bounded branch for case 08. Answer: A or B.",
    "Choose the reversible path for case 09. Answer: A or B.", "Choose the reversible path for case 10. Answer: A or B.",
    "Choose the reversible path for case 11. Answer: A or B.", "Choose the reversible path for case 12. Answer: A or B.",
    "Pick the auditable result for case 13. Answer: A or B.", "Pick the auditable result for case 14. Answer: A or B.",
    "Pick the auditable result for case 15. Answer: A or B.", "Pick the auditable result for case 16. Answer: A or B.",
    "Select the typed value for case 17. Answer: A or B.", "Select the typed value for case 18. Answer: A or B.",
    "Select the typed value for case 19. Answer: A or B.", "Select the typed value for case 20. Answer: A or B.",
    "Choose the fresh sample for case 21. Answer: A or B.", "Choose the fresh sample for case 22. Answer: A or B.",
    "Choose the fresh sample for case 23. Answer: A or B.", "Choose the fresh sample for case 24. Answer: A or B.",
    "Pick the valid context for case 25. Answer: A or B.", "Pick the valid context for case 26. Answer: A or B.",
    "Pick the valid context for case 27. Answer: A or B.", "Pick the valid context for case 28. Answer: A or B.",
    "Select the local result for case 29. Answer: A or B.", "Select the local result for case 30. Answer: A or B.",
    "Select the local result for case 31. Answer: A or B.", "Select the local result for case 32. Answer: A or B.",
};

static void stop(const char *code) { fprintf(stderr, "V29_STOP:%s\n", code); _Exit(2); }

static int32_t one(const struct llama_vocab *vocab, const char *text) {
    int32_t need = llama_tokenize(vocab, text, (int32_t)strlen(text), NULL, 0, false, false);
    if (need < 0) need = -need;
    if (need != 1) stop("TokenNotSingle");
    llama_token *tokens = calloc(1, sizeof(llama_token));
    if (tokens == NULL) stop("Allocation");
    int32_t count = llama_tokenize(vocab, text, (int32_t)strlen(text), tokens, 1, false, false);
    if (count != 1) { free(tokens); stop("TokenNotSingle"); }
    int32_t value = tokens[0]; free(tokens); return value;
}

static int32_t prompt_tokens(const struct llama_vocab *vocab, const char *text, llama_token **out) {
    int32_t need = llama_tokenize(vocab, text, (int32_t)strlen(text), NULL, 0, true, false);
    if (need < 0) need = -need;
    if (need <= 0 || need > 2048) stop("PromptTokenizationSize");
    llama_token *tokens = calloc((size_t)need, sizeof(llama_token));
    if (tokens == NULL) stop("Allocation");
    int32_t count = llama_tokenize(vocab, text, (int32_t)strlen(text), tokens, need, true, false);
    if (count != need) { free(tokens); stop("PromptTokenizationMismatch"); }
    *out = tokens; return count;
}

static Observation observe(struct llama_model *model, const llama_token *tokens, int32_t count,
    int32_t token_a, int32_t token_b, const float *control, int32_t dimension) {
    struct llama_context_params params = llama_context_default_params();
    params.n_ctx = 512; params.n_batch = 512; params.n_ubatch = 512;
    params.n_outputs_max = (uint32_t)count; params.embeddings = true;
    params.n_threads = 4; params.n_threads_batch = 4;
    struct llama_context *context = llama_init_from_model(model, params);
    if (context == NULL) stop("ContextInit");
    float *stored = NULL;
    if (control != NULL) {
        stored = calloc((size_t)dimension, sizeof(float));
        if (stored == NULL) { llama_free(context); stop("Allocation"); }
        memcpy(stored, control, (size_t)dimension * sizeof(float));
        if (llama_set_adapter_cvec(context, stored, (size_t)dimension, dimension, CONTROL_LAYER, CONTROL_LAYER) != 0) {
            free(stored); llama_free(context); stop("ControlVectorSet");
        }
    }
    struct llama_batch batch = llama_batch_init(count, 0, 1);
    if (batch.token == NULL || batch.pos == NULL || batch.n_seq_id == NULL || batch.seq_id == NULL || batch.logits == NULL) {
        free(stored); llama_free(context); stop("BatchInit");
    }
    batch.n_tokens = count;
    for (int32_t i = 0; i < count; i++) {
        batch.token[i] = tokens[i]; batch.pos[i] = i; batch.n_seq_id[i] = 1;
        batch.seq_id[i][0] = 0; batch.logits[i] = i == count - 1 ? 1 : 0;
    }
    if (llama_decode(context, batch) != 0) { llama_batch_free(batch); free(stored); llama_free(context); stop("Decode"); }
    float *embedding = llama_get_embeddings_ith(context, -1);
    float *logits = llama_get_logits_ith(context, -1);
    if (embedding == NULL || logits == NULL) { llama_batch_free(batch); free(stored); llama_free(context); stop("OutputUnavailable"); }
    Observation result = {0}; result.dimension = dimension;
    result.embedding = calloc((size_t)dimension, sizeof(float));
    if (result.embedding == NULL) { llama_batch_free(batch); free(stored); llama_free(context); stop("Allocation"); }
    result.margin = logits[token_a] - logits[token_b];
    for (int32_t i = 0; i < dimension; i++) result.embedding[i] = embedding[i];
    llama_batch_free(batch); free(stored); llama_free(context); return result;
}

static bool finite_observation(const Observation *value) {
    if (!isfinite(value->margin)) return false;
    for (int32_t i = 0; i < value->dimension; i++) if (!isfinite(value->embedding[i])) return false;
    return true;
}

static void release(Observation *value) { free(value->embedding); value->embedding = NULL; }

static float sign_for(size_t feature, int32_t coordinate) {
    uint32_t value = (uint32_t)(feature + 3) * 2654435761u;
    value ^= (uint32_t)(coordinate + 29) * 2246822519u; value ^= value >> 13;
    return (value & 1u) == 0u ? -1.0f : 1.0f;
}

static void emit(size_t trial, size_t split, const Observation *clean, const Observation *intervention) {
    float features[FULL_FEATURES];
    for (size_t feature = 0; feature < FULL_FEATURES; feature++) {
        double sum = 0.0;
        for (int32_t coordinate = 0; coordinate < clean->dimension; coordinate++) {
            sum += (double)sign_for(feature, coordinate) * (double)(intervention->embedding[coordinate] - clean->embedding[coordinate]);
        }
        features[feature] = (float)(sum / sqrt((double)clean->dimension));
    }
    printf("{\"trial\":%zu,\"split\":%zu,\"target\":%.9g,\"full\":[", trial, split, intervention->margin - clean->margin);
    for (size_t i = 0; i < FULL_FEATURES; i++) printf("%s%.9g", i == 0 ? "" : ",", features[i]);
    printf("],\"opaque\":[");
    for (size_t i = 0; i < OPAQUE_FEATURES; i++) printf("%s%.9g", i == 0 ? "" : ",", roundf(features[i] * OPAQUE_QUANTIZATION) / OPAQUE_QUANTIZATION);
    printf("],\"finite\":true}\n"); fflush(stdout);
}

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: runner_v29 <model.gguf>\n"); return 2; }
    llama_backend_init(); struct llama_model_params model_params = llama_model_default_params(); model_params.n_gpu_layers = -1;
    struct llama_model *model = llama_model_load_from_file(argv[1], model_params);
    if (model == NULL) { llama_backend_free(); stop("ModelLoad"); }
    const struct llama_vocab *vocab = llama_model_get_vocab(model);
    int32_t dimension = llama_model_n_embd(model), layers = llama_model_n_layer(model);
    if (vocab == NULL || dimension <= CONTROL_COORDINATE || layers <= CONTROL_LAYER) { llama_model_free(model); llama_backend_free(); stop("ModelDimensions"); }
    int32_t token_a = one(vocab, " A"), token_b = one(vocab, " B");
    float *control = calloc((size_t)dimension, sizeof(float)); if (control == NULL) stop("Allocation"); control[CONTROL_COORDINATE] = CONTROL_AMPLITUDE;
    for (size_t trial = 0; trial < 32; trial++) {
        llama_token *tokens = NULL; int32_t count = prompt_tokens(vocab, PROMPTS[trial], &tokens);
        Observation clean = observe(model, tokens, count, token_a, token_b, NULL, dimension);
        Observation intervention = observe(model, tokens, count, token_a, token_b, control, dimension);
        if (!finite_observation(&clean) || !finite_observation(&intervention)) stop("NonFiniteObservation");
        emit(trial, trial < 16 ? 0 : (trial < 24 ? 1 : 2), &clean, &intervention);
        release(&clean); release(&intervention); free(tokens);
    }
    free(control); llama_model_free(model); llama_backend_free(); return 0;
}
