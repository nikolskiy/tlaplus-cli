"""TLC message codes and types.

Ported from ts-output-parser/parsers/tlcCodes.ts.
"""

from enum import Enum, auto


class TlcCodeType(Enum):
    """Type of TLC message."""

    Info = auto()  # Such messages must be processed by the parser somehow
    Warning = auto()  # Such messages will be converted into warnings
    Error = auto()  # Such messages will be converted into errors
    Ignore = auto()  # Such messages will be ignored by the parser


class TlcCode:
    """TLC message code."""

    def __init__(self, num: int, code_type: TlcCodeType):
        self.num = num
        self.type = code_type


TLC_CODES: dict[int, TlcCode] = {}


def _register_code(num: int, code_type: TlcCodeType) -> TlcCode:
    tlc_code = TlcCode(num, code_type)
    TLC_CODES[num] = tlc_code
    return tlc_code


def get_tlc_code(num: int) -> TlcCode | None:
    """Get TLC code by its number."""
    return TLC_CODES.get(num)


NO_ERROR = _register_code(0, TlcCodeType.Ignore)

# Check and CheckImpl
CHECK_FAILED_TO_CHECK = _register_code(3000, TlcCodeType.Error)
CHECK_COULD_NOT_READ_TRACE = _register_code(3001, TlcCodeType.Error)

CHECK_PARAM_EXPECT_CONFIG_FILENAME = _register_code(3100, TlcCodeType.Error)
CHECK_PARAM_USAGE = _register_code(3101, TlcCodeType.Error)
CHECK_PARAM_MISSING_TLA_MODULE = _register_code(3102, TlcCodeType.Error)
CHECK_PARAM_NEED_TO_SPECIFY_CONFIG_DIR = _register_code(3103, TlcCodeType.Error)
CHECK_PARAM_WORKER_NUMBER_REQUIRED = _register_code(3104, TlcCodeType.Error)
CHECK_PARAM_WORKER_NUMBER_TOO_SMALL = _register_code(3105, TlcCodeType.Error)
CHECK_PARAM_WORKER_NUMBER_REQUIRED2 = _register_code(3106, TlcCodeType.Error)
CHECK_PARAM_DEPTH_REQUIRED = _register_code(3107, TlcCodeType.Error)
CHECK_PARAM_DEPTH_REQUIRED2 = _register_code(3108, TlcCodeType.Error)
CHECK_PARAM_TRACE_REQUIRED = _register_code(3109, TlcCodeType.Error)
CHECK_PARAM_COVREAGE_REQUIRED = _register_code(3110, TlcCodeType.Error)
CHECK_PARAM_COVREAGE_REQUIRED2 = _register_code(3111, TlcCodeType.Error)
CHECK_PARAM_COVREAGE_TOO_SMALL = _register_code(3112, TlcCodeType.Error)
CHECK_PARAM_UNRECOGNIZED = _register_code(3113, TlcCodeType.Error)
CHECK_PARAM_TOO_MANY_INPUT_FILES = _register_code(3114, TlcCodeType.Error)

SANY_PARSER_CHECK_1 = _register_code(4000, TlcCodeType.Ignore)
SANY_PARSER_CHECK_2 = _register_code(4001, TlcCodeType.Error)
SANY_PARSER_CHECK_3 = _register_code(4002, TlcCodeType.Error)

UNIT_TEST = _register_code(-123456, TlcCodeType.Ignore)

TLC_FEATURE_UNSUPPORTED = _register_code(2156, TlcCodeType.Error)
TLC_FEATURE_UNSUPPORTED_LIVENESS_SYMMETRY = _register_code(2279, TlcCodeType.Error)
TLC_FEATURE_LIVENESS_CONSTRAINTS = _register_code(2284, TlcCodeType.Warning)

GENERAL = _register_code(1000, TlcCodeType.Info)
SYSTEM_OUT_OF_MEMORY = _register_code(1001, TlcCodeType.Error)
SYSTEM_OUT_OF_MEMORY_TOO_MANY_INIT = _register_code(1002, TlcCodeType.Error)
SYSTEM_STACK_OVERFLOW = _register_code(1005, TlcCodeType.Error)

WRONG_COMMANDLINE_PARAMS_SIMULATOR = _register_code(1101, TlcCodeType.Error)
WRONG_COMMANDLINE_PARAMS_TLC = _register_code(1102, TlcCodeType.Error)

TLC_PP_PARSING_VALUE = _register_code(2000, TlcCodeType.Error)
TLC_PP_FORMATING_VALUE = _register_code(2001, TlcCodeType.Error)

TLC_METADIR_EXISTS = _register_code(2100, TlcCodeType.Error)
TLC_METADIR_CAN_NOT_BE_CREATED = _register_code(2101, TlcCodeType.Error)
TLC_INITIAL_STATE = _register_code(2102, TlcCodeType.Error)
TLC_NESTED_EXPRESSION = _register_code(2103, TlcCodeType.Error)
TLC_ASSUMPTION_FALSE = _register_code(2104, TlcCodeType.Error)
TLC_ASSUMPTION_EVALUATION_ERROR = _register_code(2105, TlcCodeType.Error)
TLC_STATE_NOT_COMPLETELY_SPECIFIED_INITIAL = _register_code(2106, TlcCodeType.Error)

TLC_INVARIANT_VIOLATED_INITIAL = _register_code(2107, TlcCodeType.Error)
TLC_PROPERTY_VIOLATED_INITIAL = _register_code(2108, TlcCodeType.Error)
TLC_STATE_NOT_COMPLETELY_SPECIFIED_NEXT = _register_code(2109, TlcCodeType.Error)
TLC_INVARIANT_VIOLATED_BEHAVIOR = _register_code(2110, TlcCodeType.Error)
TLC_INVARIANT_EVALUATION_FAILED = _register_code(2111, TlcCodeType.Error)
TLC_INVARIANT_VIOLATED_LEVEL = _register_code(2146, TlcCodeType.Error)
TLC_ACTION_PROPERTY_VIOLATED_BEHAVIOR = _register_code(2112, TlcCodeType.Error)
TLC_ACTION_PROPERTY_EVALUATION_FAILED = _register_code(2113, TlcCodeType.Error)
TLC_DEADLOCK_REACHED = _register_code(2114, TlcCodeType.Error)

TLC_STATES_AND_NO_NEXT_ACTION = _register_code(2115, TlcCodeType.Error)
TLC_TEMPORAL_PROPERTY_VIOLATED = _register_code(2116, TlcCodeType.Error)
TLC_FAILED_TO_RECOVER_NEXT = _register_code(2117, TlcCodeType.Error)
TLC_NO_STATES_SATISFYING_INIT = _register_code(2118, TlcCodeType.Error)
TLC_STRING_MODULE_NOT_FOUND = _register_code(2119, TlcCodeType.Error)

TLC_ERROR_STATE = _register_code(2120, TlcCodeType.Error)
TLC_BEHAVIOR_UP_TO_THIS_POINT = _register_code(2121, TlcCodeType.Ignore)
TLC_BACK_TO_STATE = _register_code(2122, TlcCodeType.Info)
TLC_FAILED_TO_RECOVER_INIT = _register_code(2123, TlcCodeType.Error)
TLC_REPORTER_DIED = _register_code(2124, TlcCodeType.Error)

SYSTEM_ERROR_READING_POOL = _register_code(2125, TlcCodeType.Error)
SYSTEM_CHECKPOINT_RECOVERY_CORRUPT = _register_code(2126, TlcCodeType.Error)
SYSTEM_ERROR_WRITING_POOL = _register_code(2127, TlcCodeType.Error)
SYSTEM_ERROR_CLEANING_POOL = _register_code(2270, TlcCodeType.Error)
SYSTEM_INDEX_ERROR = _register_code(2134, TlcCodeType.Error)
SYSTEM_STREAM_EMPTY = _register_code(2135, TlcCodeType.Error)
SYSTEM_FILE_NULL = _register_code(2137, TlcCodeType.Error)
SYSTEM_INTERRUPTED = _register_code(2138, TlcCodeType.Error)
SYSTEM_UNABLE_NOT_RENAME_FILE = _register_code(2160, TlcCodeType.Error)
SYSTEM_DISK_IO_ERROR_FOR_FILE = _register_code(2161, TlcCodeType.Error)
SYSTEM_METADIR_EXISTS = _register_code(2162, TlcCodeType.Error)
SYSTEM_METADIR_CREATION_ERROR = _register_code(2163, TlcCodeType.Error)
SYSTEM_UNABLE_TO_OPEN_FILE = _register_code(2167, TlcCodeType.Error)
TLC_BUG = _register_code(2128, TlcCodeType.Error)
TLC_FINGERPRINT_EXCEPTION = _register_code(2147, TlcCodeType.Error)

SYSTEM_DISKGRAPH_ACCESS = _register_code(2129, TlcCodeType.Error)

TLC_AAAAAAA = _register_code(2130, TlcCodeType.Error)
TLC_REGISTRY_INIT_ERROR = _register_code(2131, TlcCodeType.Error)
TLC_CHOOSE_ARGUMENTS_WRONG = _register_code(2164, TlcCodeType.Error)
TLC_CHOOSE_UPPER_BOUND = _register_code(2165, TlcCodeType.Error)

TLC_VALUE_ASSERT_FAILED = _register_code(2132, TlcCodeType.Error)
TLC_MODULE_VALUE_JAVA_METHOD_OVERRIDE = _register_code(2154, TlcCodeType.Error)
TLC_MODULE_VALUE_JAVA_METHOD_OVERRIDE_LOADED = _register_code(2168, TlcCodeType.Ignore)
TLC_MODULE_VALUE_JAVA_METHOD_OVERRIDE_MISMATCH = _register_code(2400, TlcCodeType.Error)
TLC_MODULE_VALUE_JAVA_METHOD_OVERRIDE_MODULE_MISMATCH = _register_code(2402, TlcCodeType.Error)
TLC_MODULE_VALUE_JAVA_METHOD_OVERRIDE_IDENTIFIER_MISMATCH = _register_code(2403, TlcCodeType.Error)
TLC_MODULE_OVERRIDE_STDOUT = _register_code(20000, TlcCodeType.Info)

TLC_FP_NOT_IN_SET = _register_code(2133, TlcCodeType.Error)
TLC_FP_VALUE_ALREADY_ON_DISK = _register_code(2166, TlcCodeType.Error)

TLC_LIVE_BEGRAPH_FAILED_TO_CONSTRUCT = _register_code(2159, TlcCodeType.Error)
TLC_PARAMETER_MUST_BE_POSTFIX = _register_code(2136, TlcCodeType.Error)
TLC_COULD_NOT_DETERMINE_SUBSCRIPT = _register_code(2139, TlcCodeType.Error)
TLC_SUBSCRIPT_CONTAIN_NO_STATE_VAR = _register_code(2140, TlcCodeType.Error)
TLC_WRONG_TUPLE_FIELD_NAME = _register_code(2141, TlcCodeType.Error)
TLC_WRONG_RECORD_FIELD_NAME = _register_code(2142, TlcCodeType.Error)
TLC_UNCHANGED_VARIABLE_CHANGED = _register_code(2143, TlcCodeType.Error)
TLC_EXCEPT_APPLIED_TO_UNKNOWN_FIELD = _register_code(2144, TlcCodeType.Error)

TLC_MODULE_TLCGET_UNDEFINED = _register_code(2145, TlcCodeType.Error)
TLC_MODULE_COMPARE_VALUE = _register_code(2155, TlcCodeType.Error)
TLC_MODULE_CHECK_MEMBER_OF = _register_code(2158, TlcCodeType.Error)
TLC_MODULE_TRANSITIVE_CLOSURE = _register_code(2157, TlcCodeType.Error)
TLC_MODULE_ARGUMENT_ERROR = _register_code(2169, TlcCodeType.Error)
TLC_MODULE_ARGUMENT_ERROR_AN = _register_code(2266, TlcCodeType.Error)
TLC_MODULE_ONE_ARGUMENT_ERROR = _register_code(2283, TlcCodeType.Error)
TLC_ARGUMENT_MISMATCH = _register_code(2170, TlcCodeType.Error)
TLC_PARSING_FAILED2 = _register_code(2171, TlcCodeType.Error)
TLC_PARSING_FAILED = _register_code(3002, TlcCodeType.Error)
TLC_TOO_MNY_POSSIBLE_STATES = _register_code(2172, TlcCodeType.Error)
TLC_ERROR_REPLACING_MODULES = _register_code(2173, TlcCodeType.Error)
SYSTEM_ERROR_READING_STATES = _register_code(2174, TlcCodeType.Error)
SYSTEM_ERROR_WRITING_STATES = _register_code(2175, TlcCodeType.Error)
TLC_MODULE_APPLYING_TO_WRONG_VALUE = _register_code(2176, TlcCodeType.Error)
TLC_MODULE_BAG_UNION1 = _register_code(2177, TlcCodeType.Error)
TLC_MODULE_OVERFLOW = _register_code(2178, TlcCodeType.Error)
TLC_MODULE_DIVISION_BY_ZERO = _register_code(2179, TlcCodeType.Error)
TLC_MODULE_NULL_POWER_NULL = _register_code(2180, TlcCodeType.Error)
TLC_MODULE_COMPUTING_CARDINALITY = _register_code(2181, TlcCodeType.Error)
TLC_MODULE_EVALUATING = _register_code(2182, TlcCodeType.Error)
TLC_MODULE_ARGUMENT_NOT_IN_DOMAIN = _register_code(2183, TlcCodeType.Error)
TLC_MODULE_APPLY_EMPTY_SEQ = _register_code(2184, TlcCodeType.Error)

TLC_SYMMETRY_SET_TOO_SMALL = _register_code(2300, TlcCodeType.Warning)
TLC_SPECIFICATION_FEATURES_TEMPORAL_QUANTIFIER = _register_code(2301, TlcCodeType.Error)

TLC_STARTING = _register_code(2185, TlcCodeType.Info)
TLC_FINISHED = _register_code(2186, TlcCodeType.Info)

# distributed TLC
TLC_DISTRIBUTED_SERVER_RUNNING = _register_code(7000, TlcCodeType.Info)
TLC_DISTRIBUTED_WORKER_REGISTERED = _register_code(7001, TlcCodeType.Info)
TLC_DISTRIBUTED_WORKER_DEREGISTERED = _register_code(7002, TlcCodeType.Info)
TLC_DISTRIBUTED_WORKER_STATS = _register_code(7003, TlcCodeType.Info)
TLC_DISTRIBUTED_SERVER_NOT_RUNNING = _register_code(7004, TlcCodeType.Info)
TLC_DISTRIBUTED_VM_VERSION = _register_code(7005, TlcCodeType.Ignore)
TLC_DISTRIBUTED_WORKER_LOST = _register_code(7006, TlcCodeType.Error)
TLC_DISTRIBUTED_EXCEED_BLOCKSIZE = _register_code(7007, TlcCodeType.Error)
TLC_DISTRIBUTED_SERVER_FPSET_WAITING = _register_code(7008, TlcCodeType.Ignore)
TLC_DISTRIBUTED_SERVER_FPSET_REGISTERED = _register_code(7009, TlcCodeType.Ignore)
TLC_DISTRIBUTED_SERVER_FINISHED = _register_code(7010, TlcCodeType.Ignore)

# errors during parsing of the model configuration
CFG_ERROR_READING_FILE = _register_code(5001, TlcCodeType.Error)
CFG_GENERAL = _register_code(5002, TlcCodeType.Error)
CFG_MISSING_ID = _register_code(5003, TlcCodeType.Error)
CFG_TWICE_KEYWORD = _register_code(5004, TlcCodeType.Error)
CFG_EXPECT_ID = _register_code(5005, TlcCodeType.Error)
CFG_EXPECTED_SYMBOL = _register_code(5006, TlcCodeType.Error)
TLC_MODE_MC = _register_code(2187, TlcCodeType.Info)
TLC_MODE_MC_DFS = _register_code(2271, TlcCodeType.Ignore)

TLC_MODE_SIMU = _register_code(2188, TlcCodeType.Ignore)
TLC_COMPUTING_INIT = _register_code(2189, TlcCodeType.Info)
TLC_COMPUTING_INIT_PROGRESS = _register_code(2269, TlcCodeType.Info)
TLC_INIT_GENERATED1 = _register_code(2190, TlcCodeType.Info)
TLC_INIT_GENERATED2 = _register_code(2191, TlcCodeType.Info)
TLC_INIT_GENERATED3 = _register_code(2207, TlcCodeType.Info)
TLC_INIT_GENERATED4 = _register_code(2208, TlcCodeType.Info)
TLC_CHECKING_TEMPORAL_PROPS = _register_code(2192, TlcCodeType.Info)
TLC_CHECKING_TEMPORAL_PROPS_END = _register_code(2267, TlcCodeType.Ignore)
TLC_SUCCESS = _register_code(2193, TlcCodeType.Info)
TLC_SEARCH_DEPTH = _register_code(2194, TlcCodeType.Ignore)
TLC_STATE_GRAPH_OUTDEGREE = _register_code(2268, TlcCodeType.Ignore)
TLC_CHECKPOINT_START = _register_code(2195, TlcCodeType.Info)
TLC_CHECKPOINT_END = _register_code(2196, TlcCodeType.Ignore)
TLC_CHECKPOINT_RECOVER_START = _register_code(2197, TlcCodeType.Ignore)
TLC_CHECKPOINT_RECOVER_END = _register_code(2198, TlcCodeType.Ignore)
TLC_STATS = _register_code(2199, TlcCodeType.Ignore)
TLC_STATS_DFID = _register_code(2204, TlcCodeType.Ignore)
TLC_STATS_SIMU = _register_code(2210, TlcCodeType.Ignore)
TLC_PROGRESS_STATS = _register_code(2200, TlcCodeType.Info)
TLC_COVERAGE_START = _register_code(2201, TlcCodeType.Ignore)
TLC_COVERAGE_END = _register_code(2202, TlcCodeType.Ignore)
TLC_CHECKPOINT_RECOVER_END_DFID = _register_code(2203, TlcCodeType.Ignore)
TLC_PROGRESS_START_STATS_DFID = _register_code(2205, TlcCodeType.Ignore)
TLC_PROGRESS_STATS_DFID = _register_code(2206, TlcCodeType.Ignore)
TLC_PROGRESS_SIMU = _register_code(2209, TlcCodeType.Info)
TLC_FP_COMPLETED = _register_code(2211, TlcCodeType.Ignore)

TLC_LIVE_IMPLIED = _register_code(2212, TlcCodeType.Ignore)
TLC_LIVE_CANNOT_HANDLE_FORMULA = _register_code(2213, TlcCodeType.Error)
TLC_LIVE_WRONG_FORMULA_FORMAT = _register_code(2214, TlcCodeType.Error)
TLC_LIVE_ENCOUNTERED_ACTIONS = _register_code(2249, TlcCodeType.Error)
TLC_LIVE_STATE_PREDICATE_NON_BOOL = _register_code(2250, TlcCodeType.Error)
TLC_LIVE_CANNOT_EVAL_FORMULA = _register_code(2251, TlcCodeType.Error)
TLC_LIVE_ENCOUNTERED_NONBOOL_PREDICATE = _register_code(2252, TlcCodeType.Error)
TLC_LIVE_FORMULA_TAUTOLOGY = _register_code(2253, TlcCodeType.Error)
TLC_LIVE_FORMULA_STATE_LEVEL = _register_code(2255, TlcCodeType.Warning)
TLC_CONFIG_NO_SPEC_BUT_PROPERTY = _register_code(2257, TlcCodeType.Warning)
TLC_LIVE_FORMULA_AND_FAIRNESS_TAUTOLOGY = _register_code(2258, TlcCodeType.Warning)
TLC_CONFIG_NO_FAIRNESS_BUT_LIVE_PROPERTY = _register_code(2259, TlcCodeType.Warning)
TLC_INVARIANT_CONSTANT_LEVEL = _register_code(2149, TlcCodeType.Warning)

TLC_EXPECTED_VALUE = _register_code(2215, TlcCodeType.Error)
TLC_EXPECTED_EXPRESSION = _register_code(2246, TlcCodeType.Error)
TLC_EXPECTED_EXPRESSION_IN_COMPUTING = _register_code(2247, TlcCodeType.Error)
TLC_EXPECTED_EXPRESSION_IN_COMPUTING2 = _register_code(2248, TlcCodeType.Error)

# state printing
TLC_STATE_PRINT1 = _register_code(2216, TlcCodeType.Info)
TLC_STATE_PRINT2 = _register_code(2217, TlcCodeType.Info)
TLC_STATE_PRINT3 = _register_code(2218, TlcCodeType.Info)
TLC_SANY_END = _register_code(2219, TlcCodeType.Info)
TLC_SANY_START = _register_code(2220, TlcCodeType.Info)
TLC_COVERAGE_MISMATCH = _register_code(2776, TlcCodeType.Ignore)
TLC_COVERAGE_VALUE = _register_code(2221, TlcCodeType.Ignore)
TLC_COVERAGE_VALUE_COST = _register_code(2775, TlcCodeType.Ignore)
TLC_COVERAGE_NEXT = _register_code(2772, TlcCodeType.Info)
TLC_COVERAGE_INIT = _register_code(2773, TlcCodeType.Info)
TLC_COVERAGE_PROPERTY = _register_code(2774, TlcCodeType.Ignore)
TLC_COVERAGE_END_OVERHEAD = _register_code(2777, TlcCodeType.Ignore)
TLC_COVERAGE_CONSTRAINT = _register_code(2778, TlcCodeType.Ignore)
TLC_COVERAGE_VAR = _register_code(2779, TlcCodeType.Ignore)

# config file errors
TLC_CONFIG_VALUE_NOT_ASSIGNED_TO_CONSTANT_PARAM = _register_code(2222, TlcCodeType.Error)
TLC_CONFIG_RHS_ID_APPEARED_AFTER_LHS_ID = _register_code(2223, TlcCodeType.Error)
TLC_CONFIG_WRONG_SUBSTITUTION = _register_code(2224, TlcCodeType.Error)
TLC_CONFIG_WRONG_SUBSTITUTION_NUMBER_OF_ARGS = _register_code(2225, TlcCodeType.Error)
TLC_CONFIG_UNDEFINED_OR_NO_OPERATOR = _register_code(2280, TlcCodeType.Error)
TLC_CONFIG_SUBSTITUTION_NON_CONSTANT = _register_code(2281, TlcCodeType.Error)
TLC_CONFIG_ID_DOES_NOT_APPEAR_IN_SPEC = _register_code(2226, TlcCodeType.Error)
TLC_CONFIG_NOT_BOTH_SPEC_AND_INIT = _register_code(2227, TlcCodeType.Error)
TLC_CONFIG_ID_REQUIRES_NO_ARG = _register_code(2228, TlcCodeType.Error)
TLC_CONFIG_SPECIFIED_NOT_DEFINED = _register_code(2229, TlcCodeType.Error)
TLC_CONFIG_ID_HAS_VALUE = _register_code(2230, TlcCodeType.Error)
TLC_CONFIG_MISSING_INIT = _register_code(2231, TlcCodeType.Error)
TLC_CONFIG_MISSING_NEXT = _register_code(2232, TlcCodeType.Error)
TLC_CONFIG_ID_MUST_NOT_BE_CONSTANT = _register_code(2233, TlcCodeType.Error)
TLC_CONFIG_OP_NO_ARGS = _register_code(2234, TlcCodeType.Error)
TLC_CONFIG_OP_NOT_IN_SPEC = _register_code(2235, TlcCodeType.Error)
TLC_CONFIG_OP_IS_EQUAL = _register_code(2236, TlcCodeType.Error)
TLC_CONFIG_SPEC_IS_TRIVIAL = _register_code(2237, TlcCodeType.Error)
TLC_CANT_HANDLE_SUBSCRIPT = _register_code(2238, TlcCodeType.Error)
TLC_CANT_HANDLE_CONJUNCT = _register_code(2239, TlcCodeType.Error)
TLC_CANT_HANDLE_TOO_MANY_NEXT_STATE_RELS = _register_code(2240, TlcCodeType.Error)
TLC_CONFIG_PROPERTY_NOT_CORRECTLY_DEFINED = _register_code(2241, TlcCodeType.Error)
TLC_CONFIG_PROPERTY_ACTION_LEVEL = _register_code(2272, TlcCodeType.Error)
TLC_CONFIG_PROPERTY_ACTION_LEVEL_SQUARE_A_SUB_V = _register_code(2273, TlcCodeType.Error)
TLC_CONFIG_PROPERTY_ACTION_LEVEL_ANGLE_A_SUB_V = _register_code(2274, TlcCodeType.Error)
TLC_CONFIG_OP_ARITY_INCONSISTENT = _register_code(2242, TlcCodeType.Error)
TLC_CONFIG_NO_STATE_TYPE = _register_code(2243, TlcCodeType.Error)
TLC_CANT_HANDLE_REAL_NUMBERS = _register_code(2244, TlcCodeType.Error)
TLC_NO_MODULES = _register_code(2245, TlcCodeType.Error)

TLC_ENABLED_WRONG_FORMULA = _register_code(2260, TlcCodeType.Error)
TLC_ENCOUNTERED_FORMULA_IN_PREDICATE = _register_code(2261, TlcCodeType.Error)
TLC_VERSION = _register_code(2262, TlcCodeType.Ignore)
TLC_USAGE = _register_code(2263, TlcCodeType.Ignore)
TLC_COUNTER_EXAMPLE = _register_code(2264, TlcCodeType.Ignore)

TLC_INTEGER_TOO_BIG = _register_code(2265, TlcCodeType.Error)
TLC_TRACE_TOO_LONG = _register_code(2282, TlcCodeType.Error)

TLC_ENVIRONMENT_JVM_GC = _register_code(2401, TlcCodeType.Warning)
TLC_TE_SPEC_GENERATION_COMPLETE = _register_code(2501, TlcCodeType.Ignore)
TLC_TE_SPEC_GENERATION_ERROR = _register_code(2502, TlcCodeType.Error)
