from enum import Enum


class OPERAND_TYPE(Enum):
    IMMEDIATE = "immediate"
    REGISTER = "register"
    TEST_ADDRESS = "test_address"
    INIT_ADDRESS = "init_address"
    ADDRESS2 = "address2"
    ADDRESS3 = "address3"
    ADDRESS4 = "address4"
    ADDRESS = "address"
    BRANCH_INDEX = "BRANCH_INDEX"


V_MUTABLE = "all"


class OPERANDS(Enum):
    Sequence_TARGET_REGISTER = "PlainTargetReg"
    TARGET_REGISTER = "TargetReg"
    FOCUS_REGISTER = "FocusReg"
    Sequence_TEMP = "plaintemp"
    Sequence_NEW_TARGET_REGISTER = "PlainTargetNewReg"
    RAND_VALUE = "randValue"
    PLAIN_FOCUS_REGISTER = "FocusSequenceReg"
    TEST_ADDRESS = "TEST_ADDRESS"
    INIT_ADDRESS = "INIT_ADDRESS"
    ADDRESS2 = 'ADDRESS2'
    ADDRESS3 = 'ADDRESS3'
    ADDRESS4 = 'ADDRESS4'
    ADDRESS = 'ADDRESS'
    BRANCH_INDEX = "BRANCH_INDEX"
    RAND_IMMEDIATE = "randImmediate"
    RAND_IMMEDIATE1 = "rand1Immediate"
    RAND_IMMEDIATE2 = "rand2Immediate"


INIT = 'init'
POST_INIT = "init-post"
DEFAULT = "default"
IMMEDIATE_ASSEMBLY = "immediate_ASSEMBLY"
END_SIMULATION = "end-simulation"
BRANCH_TARGET = "branch-target"

REGISTER_FILE = "register-file"
REGISTER = "register"
NUM_REG_FILES = "num-reg-files"
REG_FILE_SIZE = "reg-file-size"
BLOCKED_REGISTER = "blocked"
IGNORE_REGISTER = "ignore"  # registers wich should not be initialised with a random value
FORMAT = "format"
ISSUE_SLOT = 'issue-slots'
SPACE = "space"
MAX_SIZE = "max_size"
ASSEMBLY_STRUCTURE = "assembly-structure"
IMMEDIATE = 'immediate'
IMMEDIATE_OPERAND = 'immediate-operand'
SIGNAGE = "signage"
SIMD = "simd"
FLAGS = "flags"
INSTRUCTION = "instruction"
CONDITIONAL_DELIMITER = "conditional_delimiter"
CONDITIONAL = "conditional"
CONDITIONAL_READ = "conditional-read"
CONDITIONAL_SET = "conditional-set"
CONDITIONAL_SET_READ = "conditional-read-set"
SATURATION = "saturation"
ADDRESS_ALIGNMENT = "aligned"
SWITCH = "switch"
D_CACHE = "d-cache"
I_CACHE = "i-cache"
CACHE_LINES = "lines"
CACHE_BYTE_PER_LINE = "BytePerLine"
CACHE_ASSOCIATION = "associative"
CACHE_WORD_SIZE_BITS = "word-size-bits"
I_CACHE_MISS_CANDIDATE = "icacheMiss"

MANDATORY_FEATURE = "enable"

PRE_REVERSE_PROCESSOR_STATE = "randomizeProcessorStatePreReverse"
PRE_REVERSE_POST_REG_INIT_PROCESSOR_STATE = "randomizeProcessorStatePreReversePostREGRANDOM"
POST_REVERSE_PROCESSOR_STATE = "randomizeProcessorStatePostREVERSE"

IMMEDIATE_STRING = "long"
PLACEHOLDER = "#text"


class IMM_RANGE(Enum):
    START = "["
    END = "]"
    SPLIT = ":"


PROCESSOR_MEMORY_KEYWORD = "address"


class MEMORY_DESCRIPTION(Enum):
    START_ADDRESS = "start"
    OFFSET_ADDRESS = "offset"
    END_ADDRESS = "end"
    ALIGNED = "aligned"
    IMEM_OVERLAP = "imem-overlap"


DEFAULT_MAX_MEMORY_ADDRESS = 2 ** 12 - 1


class FORMAT_DESCRIPTION(Enum):
    DEFAULT = "default"
    BIN = "bin"
    HEX = "hex"
    DEC = "dec"


ASSEMBLER_ENDING = "S"

INST_LIST = 'instructions-list'
INSTR = 'instr'
REVERSE = 'reverse'
GLOBAL_PRE_SEQUENCE = "global-pre-seqeunce"
PRE_SEQUENCE_INSTR = "pre-sequence-instr"
SEQUENCE_INSTR = 'sequence-instr'
SEQUENCE_INSTR_CACHE_REPETITION = "sequence-instr-icache"
POST_SEQUENCE_INSTR = "post-sequence-instr"
PROCESSOR = "processor"
SPECIALIZATION = "specialization"
MAX_BRANCH_DISTANCE = "max-conditional-branch-distance"
FIX_IMM_VALUE = "fixed-imm-value"
SPECIAL_IMMEDIATES = "special-immediates"
INSTRUCTION_TYPE = "type"
MULTI_CYCLE_INSTRUCTION_TYPE = "-M"
NOP_INSTR = "nop"

ADDRESS = 'ADDRESS'

ERROR = 'ERROR'

COMPARISON = 'comparison'

# TODO: should come from processor.xml and Processor.py
INSTRUCTION_FEATURE_LIST = [ISSUE_SLOT, IMMEDIATE, FLAGS, ADDRESS_ALIGNMENT]
INSTRUCTION_SPECIAL_FEATURE = [SIGNAGE, SIMD, CONDITIONAL, CONDITIONAL_READ, SATURATION, SWITCH]
CONDITION_ELEMENTS = ["zero", "carry", "overflow", "negative"]

FOLDER_EXPORT_ASSEMBLY = "reversiAssembly"


def get_path_processor(architecture):
    return 'sources/' + architecture + '/processor_' + architecture + '.xml'


def get_path_instruction(architecture):
    return 'sources/' + architecture + '/instructions_' + architecture + '.xml'


def get_path_header(architecture, simulator=False):
    if simulator:
        return 'sources/' + architecture + '/header_venus_' + architecture + '.s'
    else:
        return 'sources/' + architecture + '/header_' + architecture + '.s'


def get_path_footer(architecture, simulator=False):
    if simulator:
        return 'sources/' + architecture + '/footer_venus_' + architecture + '.s'
    else:
        return 'sources/' + architecture + '/footer_' + architecture + '.s'


INSTRUCTION_DEFAULT_MODES = "default"
DELIMITER_FEATURE = '/'
INTEGER_DELIMITER = ','

TEMPORARY_CONDSEL_ENABLED = ["add", "or"]

CONDITION_PRE_INSTRUCTION = "pre-instruction"
CONDITION_POST_INSTRUCTION = "post-instruction"
CONDITION_PRE_REVERSE = "pre-reverse"
CONDITION_POST_REVERSE = "post-reverse"
