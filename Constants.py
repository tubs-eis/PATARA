from enum import Enum


class OPERAND_TYPE(Enum):
    Immediate = "immediate"
    Register = "register"
    Flag = "flag"
    Address = "address"
    Address2 = "address2"
    Address3 = "address3"
    Address4 = "address4"
    BRANCH_INDEX = "BRANCH_INDEX"

successAddress = "0xff00"


# Processor XML Constants


DELIMITER = ";"
DELIMITER_REVERSE_INSTRUCTION = "//"
DELIMITER_INSTRUCTION = '/'

# todo: should come from processor.xml and Processor.py
# v64 = 'v64'
# v32 = 'v32'
# v16 = 'v16'
# v8 = 'v8'
vMutable = "all"


TARGET_REGISTER = "TargetReg"
RAND_VALUE = "randValue"
FOCUS_REGISTER = "FocusReg"

class OPERANDS(Enum):
    TARGET_REGISTER = "TargetReg"
    RAND_VALUE = "randValue"
    FOCUS_REGISTER = "FocusReg"
    ADDRESS = 'ADDRESS'
    ADDRESS2 = 'ADDRESS2'
    ADDRESS3 = 'ADDRESS3'
    ADDRESS4 = 'ADDRESS4'
    BRANCH_INDEX = "BRANCH_INDEX"
    RAND_IMMEDIATE = "randImmediate"


INIT = 'init'
POST_INIT = "init-post"
DEFAULT = "default"
IMMEDIATE_ASSEMBLY = "immediate_ASSEMBLY"


REGISTER_FILE = "register-file"
REGISTER = "register"
VALUE_STRUCTURE = "value-structure"
VALUE_MAX = "value-max"
NUM_REG_FILES = "num-reg-files"
REG_FILE_SIZE = "reg-file-size"
BLOCKED_REGISTER = "blocked"
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
CONDITIONAL_VALUES = "conditional-values"
CONDITIONAL_READ = "conditional-read"
SATURATION = "saturation"

MANDATORY_FEATURE = "enable"


PROCESSOR_MEMORY_KEYWORD = "address"
class MEMORY_DESCRIPTION(Enum):
    startAddress = "start"
    endAddress = "end"
DEFAULT_MAX_MEMORY_ADDRESS = 2 ** 12 -1

class FORMAT_DESCRIPTION(Enum):
    default = "default"
    bin = "bin"
    hex = "hex"
    dec = "dec"

BIN = 'bin'
HEX = 'hex'
DEC = 'dec'

IMMEDIATE_LONG = 'IL'
IMMEDIATE_SHORT = "I"

class PROCESSOR_DESCRIPTION_SATURATION(Enum):
    overflow = "overflow"
    saturation = "saturation"

class PROCESSOR_DESCRIPTION_IMMEDIATE(Enum):
    short = "short"
    long = "long"

SIGNED = 'signed'
UNSIGNED = 'unsigned'

COND_SET = 'conditional-set'
COND_READ = 'conditional-read'
COND_READ_SET = 'conditional-read-set'

INST_LIST = 'instructions-list'
INSTR = 'instr'
REVERSE = 'reverse'
PROCESSOR = "processor"
SPECIALIZATION = "specialization"

ADDRESS = 'ADDRESS'

ERROR = 'ERROR'

COMPARISON = 'comparison'

# todo: should come from processor.xml and Processor.py
instructionFeatureList = [ISSUE_SLOT, IMMEDIATE, FLAGS]
instructionSpecialFeature = [SIGNAGE, SIMD, CONDITIONAL, CONDITIONAL_READ,SATURATION]
CONDITION_ELEMENTS = ["zero", "carry", "overflow", "negative"]


FOLDER_EXPORT_ASSEMBLY = "reversiAssembly"


PATH_PROCESSOR = 'sources/processor.xml'
PATH_INSTRUCTION = 'sources/instructions.xml'
PATH_INIT_REGISTER = 'sources/init_register.csv'
INSTRUCTION_DEFAULT_MODES = "default"
DELIMITER_FEATURE = '/'

class ASSEMBLY_PRAGMAS(Enum):
    define = "#define"

class ASSEMBLY_PARTIAL(Enum):
    branchIndex = "BRANCH_INDEX"



TEMPORARY_CONDSEL_ENABLED = ["add", "or"]

CONDITION_PRE_INSTRUCTION = "pre-instruction"
CONDITION_POST_INSTRUCTION = "post-instruction"
CONDITION_PRE_REVERSE = "pre-reverse"
CONDITION_POST_REVERSE = "post-reverse"