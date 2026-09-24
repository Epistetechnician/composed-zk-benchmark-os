// Lean compiler output
// Module: NanoInterp.FeatureClaim
// Imports: public import Init public meta import Init public import Std
#include <lean/lean.h>
#if defined(__clang__)
#pragma clang diagnostic ignored "-Wunused-parameter"
#pragma clang diagnostic ignored "-Wunused-label"
#elif defined(__GNUC__) && !defined(__CLANG__)
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wunused-label"
#pragma GCC diagnostic ignored "-Wunused-but-set-variable"
#endif
#ifdef __cplusplus
extern "C" {
#endif
lean_object* lean_nat_to_int(lean_object*);
lean_object* l_List_getD___redArg(lean_object*, lean_object*, lean_object*);
static lean_once_cell_t lp_ProofCarryingNanoInterp_NanoInterp_featureActivation___closed__0_once = LEAN_ONCE_CELL_INITIALIZER;
static lean_object* lp_ProofCarryingNanoInterp_NanoInterp_featureActivation___closed__0;
LEAN_EXPORT lean_object* lp_ProofCarryingNanoInterp_NanoInterp_featureActivation(lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_ProofCarryingNanoInterp_NanoInterp_featureActivation___boxed(lean_object*, lean_object*);
static lean_object* _init_lp_ProofCarryingNanoInterp_NanoInterp_featureActivation___closed__0(void){
_start:
{
lean_object* v___x_1_; lean_object* v___x_2_; 
v___x_1_ = lean_unsigned_to_nat(0u);
v___x_2_ = lean_nat_to_int(v___x_1_);
return v___x_2_;
}
}
LEAN_EXPORT lean_object* lp_ProofCarryingNanoInterp_NanoInterp_featureActivation(lean_object* v_values_3_, lean_object* v_index_4_){
_start:
{
lean_object* v___x_5_; lean_object* v___x_6_; 
v___x_5_ = lean_obj_once(&lp_ProofCarryingNanoInterp_NanoInterp_featureActivation___closed__0, &lp_ProofCarryingNanoInterp_NanoInterp_featureActivation___closed__0_once, _init_lp_ProofCarryingNanoInterp_NanoInterp_featureActivation___closed__0);
v___x_6_ = l_List_getD___redArg(v_values_3_, v_index_4_, v___x_5_);
return v___x_6_;
}
}
LEAN_EXPORT lean_object* lp_ProofCarryingNanoInterp_NanoInterp_featureActivation___boxed(lean_object* v_values_7_, lean_object* v_index_8_){
_start:
{
lean_object* v_res_9_; 
v_res_9_ = lp_ProofCarryingNanoInterp_NanoInterp_featureActivation(v_values_7_, v_index_8_);
lean_dec(v_values_7_);
return v_res_9_;
}
}
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_Std(uint8_t builtin);
static bool _G_initialized = false;
LEAN_EXPORT lean_object* initialize_ProofCarryingNanoInterp_NanoInterp_FeatureClaim(uint8_t builtin) {
lean_object * res;
if (_G_initialized) return lean_io_result_mk_ok(lean_box(0));
_G_initialized = true;
res = initialize_Init(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_Init(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_Std(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
return lean_io_result_mk_ok(lean_box(0));
}
#ifdef __cplusplus
}
#endif
