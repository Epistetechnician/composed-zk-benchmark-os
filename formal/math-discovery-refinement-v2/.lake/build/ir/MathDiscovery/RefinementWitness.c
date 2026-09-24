// Lean compiler output
// Module: MathDiscovery.RefinementWitness
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
lean_object* lean_string_length(lean_object*);
lean_object* l_String_quote(lean_object*);
lean_object* l_Bool_repr___redArg(uint8_t);
uint8_t lean_string_dec_eq(lean_object*, lean_object*);
LEAN_EXPORT uint8_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instDecidableEqRefinementWitness_decEq(lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instDecidableEqRefinementWitness_decEq___boxed(lean_object*, lean_object*);
LEAN_EXPORT uint8_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instDecidableEqRefinementWitness(lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instDecidableEqRefinementWitness___boxed(lean_object*, lean_object*);
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__0_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 3, .m_capacity = 3, .m_length = 2, .m_data = "{ "};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__0 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__0_value;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__1_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 17, .m_capacity = 17, .m_length = 16, .m_data = "protocolIdentity"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__1 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__1_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__2_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__1_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__2 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__2_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__3_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*2 + 0, .m_other = 2, .m_tag = 5}, .m_objs = {((lean_object*)(((size_t)(0) << 1) | 1)),((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__2_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__3 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__3_value;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__4_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 5, .m_capacity = 5, .m_length = 4, .m_data = " := "};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__4 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__4_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__5_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__4_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__5 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__5_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__6_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*2 + 0, .m_other = 2, .m_tag = 5}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__3_value),((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__5_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__6 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__6_value;
static lean_once_cell_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__7_once = LEAN_ONCE_CELL_INITIALIZER;
static lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__7;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__8_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 2, .m_capacity = 2, .m_length = 1, .m_data = ","};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__8 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__8_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__9_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__8_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__9 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__9_value;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__10_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 16, .m_capacity = 16, .m_length = 15, .m_data = "evaluatorDigest"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__10 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__10_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__11_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__10_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__11 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__11_value;
static lean_once_cell_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__12_once = LEAN_ONCE_CELL_INITIALIZER;
static lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__12;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__13_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 21, .m_capacity = 21, .m_length = 20, .m_data = "formalContractDigest"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__13 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__13_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__14_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__13_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__14 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__14_value;
static lean_once_cell_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__15_once = LEAN_ONCE_CELL_INITIALIZER;
static lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__15;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__16_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 14, .m_capacity = 14, .m_length = 13, .m_data = "fixtureDigest"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__16 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__16_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__17_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__16_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__17 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__17_value;
static lean_once_cell_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__18_once = LEAN_ONCE_CELL_INITIALIZER;
static lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__18;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__19_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 13, .m_capacity = 13, .m_length = 12, .m_data = "configDigest"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__19 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__19_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__20_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__19_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__20 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__20_value;
static lean_once_cell_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__21_once = LEAN_ONCE_CELL_INITIALIZER;
static lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__21;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__22_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 12, .m_capacity = 12, .m_length = 11, .m_data = "traceDigest"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__22 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__22_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__23_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__22_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__23 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__23_value;
static lean_once_cell_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__24_once = LEAN_ONCE_CELL_INITIALIZER;
static lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__24;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__25_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 21, .m_capacity = 21, .m_length = 20, .m_data = "noHiddenTruthLeakage"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__25 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__25_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__26_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__25_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__26 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__26_value;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__27_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 21, .m_capacity = 21, .m_length = 20, .m_data = "duplicateIdsRejected"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__27 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__27_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__28_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__27_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__28 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__28_value;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__29_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 25, .m_capacity = 25, .m_length = 24, .m_data = "malformedDigestsRejected"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__29 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__29_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__30_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__29_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__30 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__30_value;
static lean_once_cell_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__31_once = LEAN_ONCE_CELL_INITIALIZER;
static lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__31;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__32_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 21, .m_capacity = 21, .m_length = 20, .m_data = "permutationInvariant"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__32 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__32_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__33_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__32_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__33 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__33_value;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__34_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 21, .m_capacity = 21, .m_length = 20, .m_data = "metricGamingRejected"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__34 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__34_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__35_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__34_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__35 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__35_value;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__36_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 23, .m_capacity = 23, .m_length = 22, .m_data = "multiSeedSplitsChecked"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__36 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__36_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__37_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__36_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__37 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__37_value;
static lean_once_cell_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__38_once = LEAN_ONCE_CELL_INITIALIZER;
static lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__38;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__39_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 3, .m_capacity = 3, .m_length = 2, .m_data = " }"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__39 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__39_value;
static lean_once_cell_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__40_once = LEAN_ONCE_CELL_INITIALIZER;
static lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__40;
static lean_once_cell_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__41_once = LEAN_ONCE_CELL_INITIALIZER;
static lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__41;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__42_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__0_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__42 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__42_value;
static const lean_ctor_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__43_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_ctor_object) + sizeof(void*)*1 + 0, .m_other = 1, .m_tag = 3}, .m_objs = {((lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__39_value)}};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__43 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__43_value;
LEAN_EXPORT lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg(lean_object*);
LEAN_EXPORT lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr(lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___boxed(lean_object*, lean_object*);
static const lean_closure_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness___closed__0_value = {.m_header = {.m_rc = 0, .m_cs_sz = sizeof(lean_closure_object) + sizeof(void*)*0, .m_other = 0, .m_tag = 245}, .m_fun = (void*)lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___boxed, .m_arity = 2, .m_num_fixed = 0, .m_objs = {} };
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness___closed__0 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness___closed__0_value;
LEAN_EXPORT const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness___closed__0_value;
static const lean_string_object lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_claimCeiling___closed__0_value = {.m_header = {.m_rc = 0, .m_cs_sz = 0, .m_other = 0, .m_tag = 249}, .m_size = 38, .m_capacity = 38, .m_length = 37, .m_data = "LocalMachineCheckedFormalContractOnly"};
static const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_claimCeiling___closed__0 = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_claimCeiling___closed__0_value;
LEAN_EXPORT const lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_claimCeiling = (const lean_object*)&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_claimCeiling___closed__0_value;
LEAN_EXPORT uint8_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instDecidableEqRefinementWitness_decEq(lean_object* v_x_1_, lean_object* v_x_2_){
_start:
{
lean_object* v_protocolIdentity_3_; lean_object* v_evaluatorDigest_4_; lean_object* v_formalContractDigest_5_; lean_object* v_fixtureDigest_6_; lean_object* v_configDigest_7_; lean_object* v_traceDigest_8_; uint8_t v_noHiddenTruthLeakage_9_; uint8_t v_duplicateIdsRejected_10_; uint8_t v_malformedDigestsRejected_11_; uint8_t v_permutationInvariant_12_; uint8_t v_metricGamingRejected_13_; uint8_t v_multiSeedSplitsChecked_14_; lean_object* v_protocolIdentity_15_; lean_object* v_evaluatorDigest_16_; lean_object* v_formalContractDigest_17_; lean_object* v_fixtureDigest_18_; lean_object* v_configDigest_19_; lean_object* v_traceDigest_20_; uint8_t v_noHiddenTruthLeakage_21_; uint8_t v_duplicateIdsRejected_22_; uint8_t v_malformedDigestsRejected_23_; uint8_t v_permutationInvariant_24_; uint8_t v_metricGamingRejected_25_; uint8_t v_multiSeedSplitsChecked_26_; uint8_t v___x_27_; 
v_protocolIdentity_3_ = lean_ctor_get(v_x_1_, 0);
v_evaluatorDigest_4_ = lean_ctor_get(v_x_1_, 1);
v_formalContractDigest_5_ = lean_ctor_get(v_x_1_, 2);
v_fixtureDigest_6_ = lean_ctor_get(v_x_1_, 3);
v_configDigest_7_ = lean_ctor_get(v_x_1_, 4);
v_traceDigest_8_ = lean_ctor_get(v_x_1_, 5);
v_noHiddenTruthLeakage_9_ = lean_ctor_get_uint8(v_x_1_, sizeof(void*)*6);
v_duplicateIdsRejected_10_ = lean_ctor_get_uint8(v_x_1_, sizeof(void*)*6 + 1);
v_malformedDigestsRejected_11_ = lean_ctor_get_uint8(v_x_1_, sizeof(void*)*6 + 2);
v_permutationInvariant_12_ = lean_ctor_get_uint8(v_x_1_, sizeof(void*)*6 + 3);
v_metricGamingRejected_13_ = lean_ctor_get_uint8(v_x_1_, sizeof(void*)*6 + 4);
v_multiSeedSplitsChecked_14_ = lean_ctor_get_uint8(v_x_1_, sizeof(void*)*6 + 5);
v_protocolIdentity_15_ = lean_ctor_get(v_x_2_, 0);
v_evaluatorDigest_16_ = lean_ctor_get(v_x_2_, 1);
v_formalContractDigest_17_ = lean_ctor_get(v_x_2_, 2);
v_fixtureDigest_18_ = lean_ctor_get(v_x_2_, 3);
v_configDigest_19_ = lean_ctor_get(v_x_2_, 4);
v_traceDigest_20_ = lean_ctor_get(v_x_2_, 5);
v_noHiddenTruthLeakage_21_ = lean_ctor_get_uint8(v_x_2_, sizeof(void*)*6);
v_duplicateIdsRejected_22_ = lean_ctor_get_uint8(v_x_2_, sizeof(void*)*6 + 1);
v_malformedDigestsRejected_23_ = lean_ctor_get_uint8(v_x_2_, sizeof(void*)*6 + 2);
v_permutationInvariant_24_ = lean_ctor_get_uint8(v_x_2_, sizeof(void*)*6 + 3);
v_metricGamingRejected_25_ = lean_ctor_get_uint8(v_x_2_, sizeof(void*)*6 + 4);
v_multiSeedSplitsChecked_26_ = lean_ctor_get_uint8(v_x_2_, sizeof(void*)*6 + 5);
v___x_27_ = lean_string_dec_eq(v_protocolIdentity_3_, v_protocolIdentity_15_);
if (v___x_27_ == 0)
{
return v___x_27_;
}
else
{
uint8_t v___x_28_; 
v___x_28_ = lean_string_dec_eq(v_evaluatorDigest_4_, v_evaluatorDigest_16_);
if (v___x_28_ == 0)
{
return v___x_28_;
}
else
{
uint8_t v___x_29_; 
v___x_29_ = lean_string_dec_eq(v_formalContractDigest_5_, v_formalContractDigest_17_);
if (v___x_29_ == 0)
{
return v___x_29_;
}
else
{
uint8_t v___x_30_; 
v___x_30_ = lean_string_dec_eq(v_fixtureDigest_6_, v_fixtureDigest_18_);
if (v___x_30_ == 0)
{
return v___x_30_;
}
else
{
uint8_t v___x_31_; 
v___x_31_ = lean_string_dec_eq(v_configDigest_7_, v_configDigest_19_);
if (v___x_31_ == 0)
{
return v___x_31_;
}
else
{
uint8_t v___x_32_; 
v___x_32_ = lean_string_dec_eq(v_traceDigest_8_, v_traceDigest_20_);
if (v___x_32_ == 0)
{
return v___x_32_;
}
else
{
if (v_noHiddenTruthLeakage_9_ == 0)
{
if (v_noHiddenTruthLeakage_21_ == 0)
{
goto v___jp_37_;
}
else
{
return v_noHiddenTruthLeakage_9_;
}
}
else
{
if (v_noHiddenTruthLeakage_21_ == 0)
{
return v_noHiddenTruthLeakage_21_;
}
else
{
goto v___jp_37_;
}
}
}
v___jp_33_:
{
if (v_multiSeedSplitsChecked_14_ == 0)
{
if (v_multiSeedSplitsChecked_26_ == 0)
{
return v___x_32_;
}
else
{
return v_multiSeedSplitsChecked_14_;
}
}
else
{
return v_multiSeedSplitsChecked_26_;
}
}
v___jp_34_:
{
if (v_metricGamingRejected_13_ == 0)
{
if (v_metricGamingRejected_25_ == 0)
{
goto v___jp_33_;
}
else
{
return v_metricGamingRejected_13_;
}
}
else
{
if (v_metricGamingRejected_25_ == 0)
{
return v_metricGamingRejected_25_;
}
else
{
goto v___jp_33_;
}
}
}
v___jp_35_:
{
if (v_permutationInvariant_12_ == 0)
{
if (v_permutationInvariant_24_ == 0)
{
goto v___jp_34_;
}
else
{
return v_permutationInvariant_12_;
}
}
else
{
if (v_permutationInvariant_24_ == 0)
{
return v_permutationInvariant_24_;
}
else
{
goto v___jp_34_;
}
}
}
v___jp_36_:
{
if (v_malformedDigestsRejected_11_ == 0)
{
if (v_malformedDigestsRejected_23_ == 0)
{
goto v___jp_35_;
}
else
{
return v_malformedDigestsRejected_11_;
}
}
else
{
if (v_malformedDigestsRejected_23_ == 0)
{
return v_malformedDigestsRejected_23_;
}
else
{
goto v___jp_35_;
}
}
}
v___jp_37_:
{
if (v_duplicateIdsRejected_10_ == 0)
{
if (v_duplicateIdsRejected_22_ == 0)
{
goto v___jp_36_;
}
else
{
return v_duplicateIdsRejected_10_;
}
}
else
{
if (v_duplicateIdsRejected_22_ == 0)
{
return v_duplicateIdsRejected_22_;
}
else
{
goto v___jp_36_;
}
}
}
}
}
}
}
}
}
}
LEAN_EXPORT lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instDecidableEqRefinementWitness_decEq___boxed(lean_object* v_x_38_, lean_object* v_x_39_){
_start:
{
uint8_t v_res_40_; lean_object* v_r_41_; 
v_res_40_ = lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instDecidableEqRefinementWitness_decEq(v_x_38_, v_x_39_);
lean_dec_ref(v_x_39_);
lean_dec_ref(v_x_38_);
v_r_41_ = lean_box(v_res_40_);
return v_r_41_;
}
}
LEAN_EXPORT uint8_t lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instDecidableEqRefinementWitness(lean_object* v_x_42_, lean_object* v_x_43_){
_start:
{
uint8_t v___x_44_; 
v___x_44_ = lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instDecidableEqRefinementWitness_decEq(v_x_42_, v_x_43_);
return v___x_44_;
}
}
LEAN_EXPORT lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instDecidableEqRefinementWitness___boxed(lean_object* v_x_45_, lean_object* v_x_46_){
_start:
{
uint8_t v_res_47_; lean_object* v_r_48_; 
v_res_47_ = lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instDecidableEqRefinementWitness(v_x_45_, v_x_46_);
lean_dec_ref(v_x_46_);
lean_dec_ref(v_x_45_);
v_r_48_ = lean_box(v_res_47_);
return v_r_48_;
}
}
static lean_object* _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__7(void){
_start:
{
lean_object* v___x_62_; lean_object* v___x_63_; 
v___x_62_ = lean_unsigned_to_nat(20u);
v___x_63_ = lean_nat_to_int(v___x_62_);
return v___x_63_;
}
}
static lean_object* _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__12(void){
_start:
{
lean_object* v___x_70_; lean_object* v___x_71_; 
v___x_70_ = lean_unsigned_to_nat(19u);
v___x_71_ = lean_nat_to_int(v___x_70_);
return v___x_71_;
}
}
static lean_object* _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__15(void){
_start:
{
lean_object* v___x_75_; lean_object* v___x_76_; 
v___x_75_ = lean_unsigned_to_nat(24u);
v___x_76_ = lean_nat_to_int(v___x_75_);
return v___x_76_;
}
}
static lean_object* _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__18(void){
_start:
{
lean_object* v___x_80_; lean_object* v___x_81_; 
v___x_80_ = lean_unsigned_to_nat(17u);
v___x_81_ = lean_nat_to_int(v___x_80_);
return v___x_81_;
}
}
static lean_object* _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__21(void){
_start:
{
lean_object* v___x_85_; lean_object* v___x_86_; 
v___x_85_ = lean_unsigned_to_nat(16u);
v___x_86_ = lean_nat_to_int(v___x_85_);
return v___x_86_;
}
}
static lean_object* _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__24(void){
_start:
{
lean_object* v___x_90_; lean_object* v___x_91_; 
v___x_90_ = lean_unsigned_to_nat(15u);
v___x_91_ = lean_nat_to_int(v___x_90_);
return v___x_91_;
}
}
static lean_object* _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__31(void){
_start:
{
lean_object* v___x_101_; lean_object* v___x_102_; 
v___x_101_ = lean_unsigned_to_nat(28u);
v___x_102_ = lean_nat_to_int(v___x_101_);
return v___x_102_;
}
}
static lean_object* _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__38(void){
_start:
{
lean_object* v___x_112_; lean_object* v___x_113_; 
v___x_112_ = lean_unsigned_to_nat(26u);
v___x_113_ = lean_nat_to_int(v___x_112_);
return v___x_113_;
}
}
static lean_object* _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__40(void){
_start:
{
lean_object* v___x_115_; lean_object* v___x_116_; 
v___x_115_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__0));
v___x_116_ = lean_string_length(v___x_115_);
return v___x_116_;
}
}
static lean_object* _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__41(void){
_start:
{
lean_object* v___x_117_; lean_object* v___x_118_; 
v___x_117_ = lean_obj_once(&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__40, &lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__40_once, _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__40);
v___x_118_ = lean_nat_to_int(v___x_117_);
return v___x_118_;
}
}
LEAN_EXPORT lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg(lean_object* v_x_123_){
_start:
{
lean_object* v_protocolIdentity_124_; lean_object* v_evaluatorDigest_125_; lean_object* v_formalContractDigest_126_; lean_object* v_fixtureDigest_127_; lean_object* v_configDigest_128_; lean_object* v_traceDigest_129_; uint8_t v_noHiddenTruthLeakage_130_; uint8_t v_duplicateIdsRejected_131_; uint8_t v_malformedDigestsRejected_132_; uint8_t v_permutationInvariant_133_; uint8_t v_metricGamingRejected_134_; uint8_t v_multiSeedSplitsChecked_135_; lean_object* v___x_136_; lean_object* v___x_137_; lean_object* v___x_138_; lean_object* v___x_139_; lean_object* v___x_140_; lean_object* v___x_141_; uint8_t v___x_142_; lean_object* v___x_143_; lean_object* v___x_144_; lean_object* v___x_145_; lean_object* v___x_146_; lean_object* v___x_147_; lean_object* v___x_148_; lean_object* v___x_149_; lean_object* v___x_150_; lean_object* v___x_151_; lean_object* v___x_152_; lean_object* v___x_153_; lean_object* v___x_154_; lean_object* v___x_155_; lean_object* v___x_156_; lean_object* v___x_157_; lean_object* v___x_158_; lean_object* v___x_159_; lean_object* v___x_160_; lean_object* v___x_161_; lean_object* v___x_162_; lean_object* v___x_163_; lean_object* v___x_164_; lean_object* v___x_165_; lean_object* v___x_166_; lean_object* v___x_167_; lean_object* v___x_168_; lean_object* v___x_169_; lean_object* v___x_170_; lean_object* v___x_171_; lean_object* v___x_172_; lean_object* v___x_173_; lean_object* v___x_174_; lean_object* v___x_175_; lean_object* v___x_176_; lean_object* v___x_177_; lean_object* v___x_178_; lean_object* v___x_179_; lean_object* v___x_180_; lean_object* v___x_181_; lean_object* v___x_182_; lean_object* v___x_183_; lean_object* v___x_184_; lean_object* v___x_185_; lean_object* v___x_186_; lean_object* v___x_187_; lean_object* v___x_188_; lean_object* v___x_189_; lean_object* v___x_190_; lean_object* v___x_191_; lean_object* v___x_192_; lean_object* v___x_193_; lean_object* v___x_194_; lean_object* v___x_195_; lean_object* v___x_196_; lean_object* v___x_197_; lean_object* v___x_198_; lean_object* v___x_199_; lean_object* v___x_200_; lean_object* v___x_201_; lean_object* v___x_202_; lean_object* v___x_203_; lean_object* v___x_204_; lean_object* v___x_205_; lean_object* v___x_206_; lean_object* v___x_207_; lean_object* v___x_208_; lean_object* v___x_209_; lean_object* v___x_210_; lean_object* v___x_211_; lean_object* v___x_212_; lean_object* v___x_213_; lean_object* v___x_214_; lean_object* v___x_215_; lean_object* v___x_216_; lean_object* v___x_217_; lean_object* v___x_218_; lean_object* v___x_219_; lean_object* v___x_220_; lean_object* v___x_221_; lean_object* v___x_222_; lean_object* v___x_223_; lean_object* v___x_224_; lean_object* v___x_225_; lean_object* v___x_226_; lean_object* v___x_227_; lean_object* v___x_228_; lean_object* v___x_229_; lean_object* v___x_230_; lean_object* v___x_231_; lean_object* v___x_232_; lean_object* v___x_233_; lean_object* v___x_234_; lean_object* v___x_235_; lean_object* v___x_236_; lean_object* v___x_237_; lean_object* v___x_238_; lean_object* v___x_239_; lean_object* v___x_240_; lean_object* v___x_241_; lean_object* v___x_242_; lean_object* v___x_243_; lean_object* v___x_244_; lean_object* v___x_245_; lean_object* v___x_246_; lean_object* v___x_247_; lean_object* v___x_248_; lean_object* v___x_249_; lean_object* v___x_250_; lean_object* v___x_251_; lean_object* v___x_252_; lean_object* v___x_253_; lean_object* v___x_254_; lean_object* v___x_255_; lean_object* v___x_256_; lean_object* v___x_257_; lean_object* v___x_258_; lean_object* v___x_259_; lean_object* v___x_260_; lean_object* v___x_261_; lean_object* v___x_262_; lean_object* v___x_263_; lean_object* v___x_264_; 
v_protocolIdentity_124_ = lean_ctor_get(v_x_123_, 0);
lean_inc_ref(v_protocolIdentity_124_);
v_evaluatorDigest_125_ = lean_ctor_get(v_x_123_, 1);
lean_inc_ref(v_evaluatorDigest_125_);
v_formalContractDigest_126_ = lean_ctor_get(v_x_123_, 2);
lean_inc_ref(v_formalContractDigest_126_);
v_fixtureDigest_127_ = lean_ctor_get(v_x_123_, 3);
lean_inc_ref(v_fixtureDigest_127_);
v_configDigest_128_ = lean_ctor_get(v_x_123_, 4);
lean_inc_ref(v_configDigest_128_);
v_traceDigest_129_ = lean_ctor_get(v_x_123_, 5);
lean_inc_ref(v_traceDigest_129_);
v_noHiddenTruthLeakage_130_ = lean_ctor_get_uint8(v_x_123_, sizeof(void*)*6);
v_duplicateIdsRejected_131_ = lean_ctor_get_uint8(v_x_123_, sizeof(void*)*6 + 1);
v_malformedDigestsRejected_132_ = lean_ctor_get_uint8(v_x_123_, sizeof(void*)*6 + 2);
v_permutationInvariant_133_ = lean_ctor_get_uint8(v_x_123_, sizeof(void*)*6 + 3);
v_metricGamingRejected_134_ = lean_ctor_get_uint8(v_x_123_, sizeof(void*)*6 + 4);
v_multiSeedSplitsChecked_135_ = lean_ctor_get_uint8(v_x_123_, sizeof(void*)*6 + 5);
lean_dec_ref(v_x_123_);
v___x_136_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__5));
v___x_137_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__6));
v___x_138_ = lean_obj_once(&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__7, &lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__7_once, _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__7);
v___x_139_ = l_String_quote(v_protocolIdentity_124_);
v___x_140_ = lean_alloc_ctor(3, 1, 0);
lean_ctor_set(v___x_140_, 0, v___x_139_);
v___x_141_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_141_, 0, v___x_138_);
lean_ctor_set(v___x_141_, 1, v___x_140_);
v___x_142_ = 0;
v___x_143_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_143_, 0, v___x_141_);
lean_ctor_set_uint8(v___x_143_, sizeof(void*)*1, v___x_142_);
v___x_144_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_144_, 0, v___x_137_);
lean_ctor_set(v___x_144_, 1, v___x_143_);
v___x_145_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__9));
v___x_146_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_146_, 0, v___x_144_);
lean_ctor_set(v___x_146_, 1, v___x_145_);
v___x_147_ = lean_box(1);
v___x_148_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_148_, 0, v___x_146_);
lean_ctor_set(v___x_148_, 1, v___x_147_);
v___x_149_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__11));
v___x_150_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_150_, 0, v___x_148_);
lean_ctor_set(v___x_150_, 1, v___x_149_);
v___x_151_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_151_, 0, v___x_150_);
lean_ctor_set(v___x_151_, 1, v___x_136_);
v___x_152_ = lean_obj_once(&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__12, &lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__12_once, _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__12);
v___x_153_ = l_String_quote(v_evaluatorDigest_125_);
v___x_154_ = lean_alloc_ctor(3, 1, 0);
lean_ctor_set(v___x_154_, 0, v___x_153_);
v___x_155_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_155_, 0, v___x_152_);
lean_ctor_set(v___x_155_, 1, v___x_154_);
v___x_156_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_156_, 0, v___x_155_);
lean_ctor_set_uint8(v___x_156_, sizeof(void*)*1, v___x_142_);
v___x_157_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_157_, 0, v___x_151_);
lean_ctor_set(v___x_157_, 1, v___x_156_);
v___x_158_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_158_, 0, v___x_157_);
lean_ctor_set(v___x_158_, 1, v___x_145_);
v___x_159_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_159_, 0, v___x_158_);
lean_ctor_set(v___x_159_, 1, v___x_147_);
v___x_160_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__14));
v___x_161_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_161_, 0, v___x_159_);
lean_ctor_set(v___x_161_, 1, v___x_160_);
v___x_162_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_162_, 0, v___x_161_);
lean_ctor_set(v___x_162_, 1, v___x_136_);
v___x_163_ = lean_obj_once(&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__15, &lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__15_once, _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__15);
v___x_164_ = l_String_quote(v_formalContractDigest_126_);
v___x_165_ = lean_alloc_ctor(3, 1, 0);
lean_ctor_set(v___x_165_, 0, v___x_164_);
v___x_166_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_166_, 0, v___x_163_);
lean_ctor_set(v___x_166_, 1, v___x_165_);
v___x_167_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_167_, 0, v___x_166_);
lean_ctor_set_uint8(v___x_167_, sizeof(void*)*1, v___x_142_);
v___x_168_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_168_, 0, v___x_162_);
lean_ctor_set(v___x_168_, 1, v___x_167_);
v___x_169_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_169_, 0, v___x_168_);
lean_ctor_set(v___x_169_, 1, v___x_145_);
v___x_170_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_170_, 0, v___x_169_);
lean_ctor_set(v___x_170_, 1, v___x_147_);
v___x_171_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__17));
v___x_172_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_172_, 0, v___x_170_);
lean_ctor_set(v___x_172_, 1, v___x_171_);
v___x_173_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_173_, 0, v___x_172_);
lean_ctor_set(v___x_173_, 1, v___x_136_);
v___x_174_ = lean_obj_once(&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__18, &lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__18_once, _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__18);
v___x_175_ = l_String_quote(v_fixtureDigest_127_);
v___x_176_ = lean_alloc_ctor(3, 1, 0);
lean_ctor_set(v___x_176_, 0, v___x_175_);
v___x_177_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_177_, 0, v___x_174_);
lean_ctor_set(v___x_177_, 1, v___x_176_);
v___x_178_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_178_, 0, v___x_177_);
lean_ctor_set_uint8(v___x_178_, sizeof(void*)*1, v___x_142_);
v___x_179_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_179_, 0, v___x_173_);
lean_ctor_set(v___x_179_, 1, v___x_178_);
v___x_180_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_180_, 0, v___x_179_);
lean_ctor_set(v___x_180_, 1, v___x_145_);
v___x_181_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_181_, 0, v___x_180_);
lean_ctor_set(v___x_181_, 1, v___x_147_);
v___x_182_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__20));
v___x_183_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_183_, 0, v___x_181_);
lean_ctor_set(v___x_183_, 1, v___x_182_);
v___x_184_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_184_, 0, v___x_183_);
lean_ctor_set(v___x_184_, 1, v___x_136_);
v___x_185_ = lean_obj_once(&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__21, &lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__21_once, _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__21);
v___x_186_ = l_String_quote(v_configDigest_128_);
v___x_187_ = lean_alloc_ctor(3, 1, 0);
lean_ctor_set(v___x_187_, 0, v___x_186_);
v___x_188_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_188_, 0, v___x_185_);
lean_ctor_set(v___x_188_, 1, v___x_187_);
v___x_189_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_189_, 0, v___x_188_);
lean_ctor_set_uint8(v___x_189_, sizeof(void*)*1, v___x_142_);
v___x_190_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_190_, 0, v___x_184_);
lean_ctor_set(v___x_190_, 1, v___x_189_);
v___x_191_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_191_, 0, v___x_190_);
lean_ctor_set(v___x_191_, 1, v___x_145_);
v___x_192_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_192_, 0, v___x_191_);
lean_ctor_set(v___x_192_, 1, v___x_147_);
v___x_193_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__23));
v___x_194_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_194_, 0, v___x_192_);
lean_ctor_set(v___x_194_, 1, v___x_193_);
v___x_195_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_195_, 0, v___x_194_);
lean_ctor_set(v___x_195_, 1, v___x_136_);
v___x_196_ = lean_obj_once(&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__24, &lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__24_once, _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__24);
v___x_197_ = l_String_quote(v_traceDigest_129_);
v___x_198_ = lean_alloc_ctor(3, 1, 0);
lean_ctor_set(v___x_198_, 0, v___x_197_);
v___x_199_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_199_, 0, v___x_196_);
lean_ctor_set(v___x_199_, 1, v___x_198_);
v___x_200_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_200_, 0, v___x_199_);
lean_ctor_set_uint8(v___x_200_, sizeof(void*)*1, v___x_142_);
v___x_201_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_201_, 0, v___x_195_);
lean_ctor_set(v___x_201_, 1, v___x_200_);
v___x_202_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_202_, 0, v___x_201_);
lean_ctor_set(v___x_202_, 1, v___x_145_);
v___x_203_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_203_, 0, v___x_202_);
lean_ctor_set(v___x_203_, 1, v___x_147_);
v___x_204_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__26));
v___x_205_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_205_, 0, v___x_203_);
lean_ctor_set(v___x_205_, 1, v___x_204_);
v___x_206_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_206_, 0, v___x_205_);
lean_ctor_set(v___x_206_, 1, v___x_136_);
v___x_207_ = l_Bool_repr___redArg(v_noHiddenTruthLeakage_130_);
v___x_208_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_208_, 0, v___x_163_);
lean_ctor_set(v___x_208_, 1, v___x_207_);
v___x_209_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_209_, 0, v___x_208_);
lean_ctor_set_uint8(v___x_209_, sizeof(void*)*1, v___x_142_);
v___x_210_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_210_, 0, v___x_206_);
lean_ctor_set(v___x_210_, 1, v___x_209_);
v___x_211_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_211_, 0, v___x_210_);
lean_ctor_set(v___x_211_, 1, v___x_145_);
v___x_212_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_212_, 0, v___x_211_);
lean_ctor_set(v___x_212_, 1, v___x_147_);
v___x_213_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__28));
v___x_214_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_214_, 0, v___x_212_);
lean_ctor_set(v___x_214_, 1, v___x_213_);
v___x_215_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_215_, 0, v___x_214_);
lean_ctor_set(v___x_215_, 1, v___x_136_);
v___x_216_ = l_Bool_repr___redArg(v_duplicateIdsRejected_131_);
v___x_217_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_217_, 0, v___x_163_);
lean_ctor_set(v___x_217_, 1, v___x_216_);
v___x_218_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_218_, 0, v___x_217_);
lean_ctor_set_uint8(v___x_218_, sizeof(void*)*1, v___x_142_);
v___x_219_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_219_, 0, v___x_215_);
lean_ctor_set(v___x_219_, 1, v___x_218_);
v___x_220_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_220_, 0, v___x_219_);
lean_ctor_set(v___x_220_, 1, v___x_145_);
v___x_221_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_221_, 0, v___x_220_);
lean_ctor_set(v___x_221_, 1, v___x_147_);
v___x_222_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__30));
v___x_223_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_223_, 0, v___x_221_);
lean_ctor_set(v___x_223_, 1, v___x_222_);
v___x_224_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_224_, 0, v___x_223_);
lean_ctor_set(v___x_224_, 1, v___x_136_);
v___x_225_ = lean_obj_once(&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__31, &lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__31_once, _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__31);
v___x_226_ = l_Bool_repr___redArg(v_malformedDigestsRejected_132_);
v___x_227_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_227_, 0, v___x_225_);
lean_ctor_set(v___x_227_, 1, v___x_226_);
v___x_228_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_228_, 0, v___x_227_);
lean_ctor_set_uint8(v___x_228_, sizeof(void*)*1, v___x_142_);
v___x_229_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_229_, 0, v___x_224_);
lean_ctor_set(v___x_229_, 1, v___x_228_);
v___x_230_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_230_, 0, v___x_229_);
lean_ctor_set(v___x_230_, 1, v___x_145_);
v___x_231_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_231_, 0, v___x_230_);
lean_ctor_set(v___x_231_, 1, v___x_147_);
v___x_232_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__33));
v___x_233_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_233_, 0, v___x_231_);
lean_ctor_set(v___x_233_, 1, v___x_232_);
v___x_234_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_234_, 0, v___x_233_);
lean_ctor_set(v___x_234_, 1, v___x_136_);
v___x_235_ = l_Bool_repr___redArg(v_permutationInvariant_133_);
v___x_236_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_236_, 0, v___x_163_);
lean_ctor_set(v___x_236_, 1, v___x_235_);
v___x_237_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_237_, 0, v___x_236_);
lean_ctor_set_uint8(v___x_237_, sizeof(void*)*1, v___x_142_);
v___x_238_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_238_, 0, v___x_234_);
lean_ctor_set(v___x_238_, 1, v___x_237_);
v___x_239_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_239_, 0, v___x_238_);
lean_ctor_set(v___x_239_, 1, v___x_145_);
v___x_240_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_240_, 0, v___x_239_);
lean_ctor_set(v___x_240_, 1, v___x_147_);
v___x_241_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__35));
v___x_242_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_242_, 0, v___x_240_);
lean_ctor_set(v___x_242_, 1, v___x_241_);
v___x_243_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_243_, 0, v___x_242_);
lean_ctor_set(v___x_243_, 1, v___x_136_);
v___x_244_ = l_Bool_repr___redArg(v_metricGamingRejected_134_);
v___x_245_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_245_, 0, v___x_163_);
lean_ctor_set(v___x_245_, 1, v___x_244_);
v___x_246_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_246_, 0, v___x_245_);
lean_ctor_set_uint8(v___x_246_, sizeof(void*)*1, v___x_142_);
v___x_247_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_247_, 0, v___x_243_);
lean_ctor_set(v___x_247_, 1, v___x_246_);
v___x_248_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_248_, 0, v___x_247_);
lean_ctor_set(v___x_248_, 1, v___x_145_);
v___x_249_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_249_, 0, v___x_248_);
lean_ctor_set(v___x_249_, 1, v___x_147_);
v___x_250_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__37));
v___x_251_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_251_, 0, v___x_249_);
lean_ctor_set(v___x_251_, 1, v___x_250_);
v___x_252_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_252_, 0, v___x_251_);
lean_ctor_set(v___x_252_, 1, v___x_136_);
v___x_253_ = lean_obj_once(&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__38, &lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__38_once, _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__38);
v___x_254_ = l_Bool_repr___redArg(v_multiSeedSplitsChecked_135_);
v___x_255_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_255_, 0, v___x_253_);
lean_ctor_set(v___x_255_, 1, v___x_254_);
v___x_256_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_256_, 0, v___x_255_);
lean_ctor_set_uint8(v___x_256_, sizeof(void*)*1, v___x_142_);
v___x_257_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_257_, 0, v___x_252_);
lean_ctor_set(v___x_257_, 1, v___x_256_);
v___x_258_ = lean_obj_once(&lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__41, &lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__41_once, _init_lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__41);
v___x_259_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__42));
v___x_260_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_260_, 0, v___x_259_);
lean_ctor_set(v___x_260_, 1, v___x_257_);
v___x_261_ = ((lean_object*)(lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg___closed__43));
v___x_262_ = lean_alloc_ctor(5, 2, 0);
lean_ctor_set(v___x_262_, 0, v___x_260_);
lean_ctor_set(v___x_262_, 1, v___x_261_);
v___x_263_ = lean_alloc_ctor(4, 2, 0);
lean_ctor_set(v___x_263_, 0, v___x_258_);
lean_ctor_set(v___x_263_, 1, v___x_262_);
v___x_264_ = lean_alloc_ctor(6, 1, 1);
lean_ctor_set(v___x_264_, 0, v___x_263_);
lean_ctor_set_uint8(v___x_264_, sizeof(void*)*1, v___x_142_);
return v___x_264_;
}
}
LEAN_EXPORT lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr(lean_object* v_x_265_, lean_object* v_prec_266_){
_start:
{
lean_object* v___x_267_; 
v___x_267_ = lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___redArg(v_x_265_);
return v___x_267_;
}
}
LEAN_EXPORT lean_object* lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr___boxed(lean_object* v_x_268_, lean_object* v_prec_269_){
_start:
{
lean_object* v_res_270_; 
v_res_270_ = lp_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_instReprRefinementWitness_repr(v_x_268_, v_prec_269_);
lean_dec(v_prec_269_);
return v_res_270_;
}
}
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_Std(uint8_t builtin);
static bool _G_initialized = false;
LEAN_EXPORT lean_object* initialize_math_x2ddiscovery_x2drefinement_x2dv2_MathDiscovery_RefinementWitness(uint8_t builtin) {
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
