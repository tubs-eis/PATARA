#!/usr/bin/python3
import argparse
import multiprocessing
import os
import subprocess
import time
from os.path import exists, isdir

from Constants import ADDRESS_ALIGNMENT, CONDITIONAL, CONDITIONAL_READ, FOLDER_EXPORT_ASSEMBLY, IMMEDIATE, SATURATION, SIGNAGE, SIMD, SWITCH, get_path_header, get_path_footer
import Constants
from extract_rv_instr_from_assembly import count_instructions
from util.ConditionalExecutionCode import ConditionalExecutionCode
from util.DataBank import DataBank
from util.Processor import Processor
from util.RandomOptions import RandomOptions
from util.Stack import Stack
from util.TestInstruction import TestInstruction


def existsDirectory(path):
    if exists(path):
        return isdir(path)
    else:
        return False


def createDirectoryIfNew(directory):
    if not exists(directory):
        command = "mkdir -p " + directory
        subprocess.run(command, shell=True)


def getFilesInDir(directory):
    lst = os.listdir(directory)  # your directory path
    return len(lst)

def _get_max_arg_len(args):
    ## Calculate the maximum length of all option strings for alignment
    return max([len(key) for key in list(vars(args).keys())])

def print_arguments(args, parser):
    # Create a list of non-default group titles (skip 'positional arguments' and 'optional arguments')
    non_default_groups = [group for group in parser._action_groups]
    
    # Calculate the maximum length of all option strings for alignment
    max_len = _get_max_arg_len(args)

    # Print arguments by group
    for group in non_default_groups:
        empty_group = len([action for action in group._group_actions if action.dest in args]) == 0
        if not empty_group:
            print(f"{group.title}:")
            for action in group._group_actions:
                if action.dest != 'help':
                    value = getattr(args, action.dest)
                    # Find the longest option string for this action for consistent printing
                    # longest_option = max(action.option_strings, key=len)
                    key_word = next((option for option in action.option_strings if option.startswith('--')), None)
                    print(f"  {key_word.ljust(max_len + 4)}: {value}")
            print()  # Blank line between groups


def write_files(prefix, singleInstructionTests, runID, loopIteration):
    fileCount = 0
    for instructionName, code in singleInstructionTests.items():
        filestring = prefix+"_" + instructionName + "_" + str(loopIteration) +"_" + str(fileCount) +"_"+ runID+ "." + Processor().get_assembler_ending()
        exportFile = os.path.join(FOLDER_EXPORT_ASSEMBLY, filestring)

        rawfile = open(exportFile, 'w')
        rawfile.write(header)
        rawfile.write(code)
        rawfile.write(footer)
        rawfile.close()

        fileCount += 1
    

def create_basic_instruciton_test(runID, loopIteration, args):
    singleInstruction = args.singleInstruction
    random_ops = RandomOptions(args)
    Processor(architecture=args.architecture, cacheMiss=float(args.dcacheMiss),
              newMemoryBlock=float(args.newMemoryBlock))
    stack = Stack(args.architecture, args.icacheMiss,enabled_extensions=args.isa_extensions)
    
    singleInstructionTests, testcases, instrCount = stack.create_basic_instruction_test(random_ops=random_ops, singleInstruction=singleInstruction)
    write_files("basic", singleInstructionTests, runID, loopIteration)
    
    return testcases, instrCount, len(singleInstructionTests)
    
    
def create_complete_instruction_test(runID, loopIteration, args):
    singleInstruction = args.singleInstruction
    random_ops = RandomOptions(args)
    Processor(architecture=args.architecture, cacheMiss=float(args.dcacheMiss),
              newMemoryBlock=float(args.newMemoryBlock))
    stack = Stack(args.architecture, args.icacheMiss,enabled_extensions=args.isa_extensions)
    
    singleInstructionTests, testcases, instrCount = stack.create_complete_instruction_test(random_ops=random_ops, singleInstruction=singleInstruction)
    write_files("complete",singleInstructionTests, runID, loopIteration)
    
    return testcases, instrCount, len(singleInstructionTests)


def createSequence(runID, loopIteration, args):
    random_ops = RandomOptions(args)
    Processor(architecture=args.architecture, cacheMiss=float(args.dcacheMiss),
              newMemoryBlock=float(args.newMemoryBlock))
    stack = Stack(args.architecture, args.icacheMiss,enabled_extensions=args.isa_extensions)
    
    instructions = stack.generateSequenceInstructionsList(args.sequenceLength)
    num_test_instr = 0
    total_instructions = 0
    file_count = 0
    for instructionList in instructions:
        code, testInstr, instrCount = stack.createSequenceInstructions(instructionList, random_ops, args.immediate,
                                                                        args.switch_prob, args.forwarding,
                                                                        args.specialImmediates,
                                                                        forwardingStallProb=args.sequenceStall)
        num_test_instr += testInstr
        total_instructions += instrCount
        # export file
        filestring = "sequence"
        filestring += "_switch_" + str(int(args.switch_prob * 100))
        filestring += "_forwarding_" + str(args.forwarding)
        filestring += "_forwardStall_" + str(int(args.sequenceStall * 100))
        filestring += "_specialImms_" + str(int(args.specialImmediates * 100))
        filestring += "_dcache_" + str(int(args.dcacheMiss * 100))
        filestring += "_newMemBlock_" + str(int(newMemoryBlock * 100))
        filestring += "_" + str(loopIteration)
        filestring += "_" + str(file_count)
        filestring += "_"+ runID
        filestring += "." + Processor().get_assembler_ending()
        exportFile = os.path.join(FOLDER_EXPORT_ASSEMBLY, filestring)

        rawfile = open(exportFile, 'w')
        rawfile.write(header)
        rawfile.write(code)
        rawfile.write(footer)
        rawfile.close()

        file_count += 1
        # count_instructions(exportFile, PATH_RISC_V, RESULT_FILE)
    return num_test_instr, total_instructions, file_count


def createInterleaving(runID, loopIteration, args):
    random_ops = RandomOptions(args)
    Processor(architecture=args.architecture, cacheMiss=float(args.dcacheMiss),
              newMemoryBlock=float(args.newMemoryBlock))
    stack = Stack(args.architecture, args.icacheMiss,enabled_extensions=args.isa_extensions)
    
    filestring = "interleaving"
    filestring += "_switch_" + str(int(args.switch_prob * 100))
    filestring += "_specialImms_" + str(int(args.specialImmediates * 100))
    filestring += "_dcache_" + str(int(args.dcacheMiss * 100))
    filestring += "_newMemBlock_" + str(int(args.newMemoryBlock * 100))
    filestring += "_" + str(loopIteration)
    filestring += "_" + runID
    filestring += "." + Processor().get_assembler_ending()

    code, testInstr, instrCount = stack.createInterleavingInstructions(random_ops, args.isa_repetition, args.immediate,
                                                                        args.switch_prob,
                                                                        specialImmediates=args.specialImmediates, max_instructions=args.max_interleaving_instructions)


    exportFile = os.path.join(FOLDER_EXPORT_ASSEMBLY, filestring)
    rawfile = open(exportFile, 'w')
    rawfile.write(header)
    rawfile.write(code)
    rawfile.write(footer)
    rawfile.close()

    return testInstr, instrCount, 1
    


if __name__ == '__main__':
    start_time = time.time()
    parser = argparse.ArgumentParser()

    argument_options = parser.add_argument_group('Options')
    argument_options.add_argument("-a", "--architecture",
                          help="Architecture description folder in sources/ARCHITECTURE. Defaults to rv32imc.",
                          default="rv32imc")
    argument_options.add_argument("--isa_extensions",
                                  help="Describe the ISA extensions used (is multiple extensions are valid, append them). Defaults to all extensions. Possible values for RISC-V are: 'i','m', 'im'",
                                  default="")
    argument_options.add_argument("-r", "--files", "--repetitions", help="How many assembly files to generate for each configuration. Defaults to 1.",
                          default="1")
    argument_options.add_argument("-t","--threads", help="How many threads to use for the generation. Defaults to 1.",type=int,
                          default="1")
    argument_options.add_argument("--immediate",
                          help="Probability of immediate generated. Range from 0.0 - 1.0. Defaults to 0.5.", type=float,    
                          default="0.5")
    argument_options.add_argument("--specialImmediates", help="Create Sequences which test Special immediates. Defaults to 0.", type=float,
                          default="0.0")
    argument_options.add_argument("--switch_prob","--switch",
                          help="Probability of instructions with switched focusReg and randValue generated. Range from 0.0 - 1.0. Defaults to 0.5.",type=float,
                          default="0.5")
    
    
    
    arguments_basic = parser.add_argument_group('Single Instruction Test Options')
    arguments_basic.add_argument("--basicInstruction",
                          help="Instructions for all basic instructions. Random value is always in source operand 2.",
                          action="store_true")
    # todo: implement for KAVUAKA
    arguments_basic.add_argument("--completeInstruction","-c",
                          help="Will go through all combinations of basic + switch the random and focus register (used for forwarding).",
                          action="store_true")
    
    
    arguments_interleaving = parser.add_argument_group('Interleaving Options')
    arguments_interleaving.add_argument("-i", "--interleaving", help="interleaving Test.", action="store_true")
    arguments_interleaving.add_argument("--max_interleaving_instructions", type=int,
                            help="Maximum number of total instructions in the interleaving test. Defaults to -1, no limits on total number of instructions.",
                            default="-1")
    arguments_interleaving.add_argument("-l", "--isa_repetition", "--level", help="Number of times that each instruction of the ISA will be used in the interleaving test. max_interleaving_instruction always overrides the total test instruction, if max_interleaving_instruction is -1, the total number of instructions to be used in the sequence is defined by the maximum number of instructions in the instruction set multiplied by the number of levels. Defaults to 1.",type=int,
                          default="1")
    arguments_interleaving.add_argument("--icacheMiss",
                          help="Probability of incuring Instruction Cache miss. Defaults to 0.5. Not supported on sequences!",
                          default="0.5")
    
    
    arguments_sequence = parser.add_argument_group('Sequence Options')
    arguments_sequence.add_argument("-s", "--sequence",
                          help="if set an extra instruction path with only plain instructions gets created and compares it results with the normal instruction path.",
                          action="store_true")
    arguments_sequence.add_argument("-f", "--forwarding",
                          help="Test Sequence with FORWARDING instruction inside of the sequence. Defaults to 0.",type=int,
                          default=0)
    arguments_sequence.add_argument("--sequenceLength",
                          help="Give the list of Sequences to iterate through. Defaults to 4. Only works on sequences!",type=int,
                          default=4)
    arguments_sequence.add_argument("--sequenceStall",
                          help="Probability to stall the pipeline between base instructions with forwarding holes. Defaults to 0.5",
                          default=0.5)

    randomization_group = parser.add_argument_group('Randomization Options')
    randomization_group.add_argument("--randomize_init_load", help="Randomize register-file in the init-randomization (immediatly after header) with load instructions. Defaults to False (and randomization with immediates).", action="store_true", default=False)
    randomization_group.add_argument("--randomize_init_immediate", help="Randomize register-file in the init-randomization (immediatly after header) with immediate values. Defaults to False (and randomization with load instructions).", action="store_true", default=False)
    randomization_group.add_argument("--randomize_processor_state", help="Randomize processor-state between modification and reverse instruction. This option allone will not randomize the register-file ( use --randomize_processor_state_load or randomize_processor_state_immediate). Hint: Enabling one randomization method, will automatically also set this option. Defaults to False.", action="store_true", default=False)
    randomization_group.add_argument("--randomize_processor_state_load", help="Randomize register-file in the processor-state-randomization between modification and reverse with load instructions. Defaults to False.", action="store_true", default=False)
    randomization_group.add_argument("--randomize_processor_state_immediate", help="Randomize register-file in the processor-state-randomization between modification and reverse with immediate values. Defaults to False.", action="store_true", default=False)
    
    
    arguments_template = parser.add_argument_group('Template Options')
    arguments_template.add_argument("--not_randomize", help="Do not randomize the header. Will use non_randomized.asm header and footer. Defaults to False (will randomize register-file after header. For randomization method see randomize_init_load)", default=False, action="store_true")
    arguments_template.add_argument("--header", help="Alternative path to header file. Defaults to targets/target/header_{TARGET}_randomized.s", default="")
    arguments_template.add_argument("--footer", help="Alternative path to footer file. Defaults to targets/target/footer_{TARGET}_randomized.s", default="")

        
    optional = parser.add_argument_group('Data Memory Options')
    optional.add_argument("--newMemoryBlock",
                          help="Probability of starting a new memory block region. Defaults to 0.0.", type=float, default="0.0")
    optional.add_argument("--dcacheMiss", help="Probability of incuring Data Cache misses. Defaults to 0.5.",type=float,
                          default="0.5")
    
    
    arguments_debug = parser.add_argument_group('Debug Options')
    arguments_debug.add_argument("-b", "--singleInstruction",
                          help="Test Single Instruction. In combination with basicInstruction and completeInstruction, will only generate all variants for this single instruction.",
                          default="")
    arguments_debug.add_argument("--clean", help="Clean the export directory", action="store_true", default=False)
    arguments_debug.add_argument("--test", help="Test the program. Will not create IDs for easier handling.", action="store_true", default=False)
    
    RESULT_FILE = "results.txt"
    if exists(RESULT_FILE):
        os.remove(RESULT_FILE)

    # PATH_RISC_V = "/localtemp2/coverage_share_tmp/vpro_sys_optimized/APPS/EISV/core_verification/test_frameworks"

    args = parser.parse_args()
    
    print_arguments(args, parser)
    
    Constants.TEST_ENABLED = args.test
    
    random_ops = RandomOptions(args)
    
    if args.clean:
        # rm files from reversiAssembly folder
        print(f"Cleaning Export Directory {FOLDER_EXPORT_ASSEMBLY}")
        command = "rm " + FOLDER_EXPORT_ASSEMBLY + "/*"
        print(command)
        os.system(command)
    

    dCacheMisses = float(args.dcacheMiss)
    newMemoryBlock = float(args.newMemoryBlock)

    Processor(architecture=args.architecture, cacheMiss=float(dCacheMisses),
              newMemoryBlock=float(newMemoryBlock))

    sequenceLength = int(args.sequenceLength)

    switchProbability = float(args.switch_prob)
    depth = int(args.isa_repetition)
    immediateProbability = float(args.immediate)
    files = int(args.files)
    singleInstruction = args.singleInstruction
    stack = Stack(args.architecture, args.icacheMiss,enabled_extensions=args.isa_extensions)
    instruction_set = DataBank().get_instruction_list()
    v = ConditionalExecutionCode(args.architecture, instruction_set)
    # prepare Export folder
    createDirectoryIfNew(FOLDER_EXPORT_ASSEMBLY)
    forwardingHole = int(args.forwarding)
    specialImmediates = float(args.specialImmediates)
    forwardingStallProb = float(args.sequenceStall)
    
    
    MAX_INTERLEAVING_INSTRUCTIONS = args.max_interleaving_instructions
    

    # import Constant files
    headerFile = open(get_path_header(args.architecture, random_opts=random_ops, header_path=args.header), 'r')
    header = headerFile.read()
    headerFile.close()
    footerFile = open(get_path_footer(args.architecture, random_opts=random_ops, footer_path=args.footer), 'r')
    footer = footerFile.read()
    footerFile.close()
    


    # # #####################################################################################
    # # ## Debugging: Test Single Configuration
    # # #####################################################################################
    # # basic_add_Sat-saturation_Sig-unsigned_simd-v32
    # stack.generateInstructionsList(1, singleInstruction)
    # testInstruction: TestInstruction = stack._instructionsList[0]
    # # set immediate 
    # immidiateAttr = "long"# "short"
    # # basic_and_simd-v16_0_1713445684
    # # complete_or_I-long_simd-v64
    
    
    # testInstruction.setEnableFeatureName(ADDRESS_ALIGNMENT, None)
    # # testInstruction.setEnableFeatureName(SIGNAGE, "unsigned")
    # testInstruction.setEnableFeatureName(SIMD, "v64")
    # testInstruction.setEnableFeatureName(CONDITIONAL, None)
    # testInstruction.setEnableFeatureName(SATURATION, "overflow")
    # # testInstruction.setEnableFeatureName(CONDITIONAL, CONDITIONAL_READ)
    # # testInstruction.setEnableFeature(CONDITIONAL_READ, "negative")
    # testInstruction.setEnableFeatureName(IMMEDIATE, immidiateAttr)
    # # testInstruction.setEnableFeatureName(SWITCH, switchAttr)
    # print(stack._generate_single_test_assembly(testInstruction, 0, random_ops))
    # n=3

    
    runID = str(int(time.time())) if not args.test else ""
    numberTestInstructions = 0
    totalInstructions = 0
    fileCount =0
    original_fileCount = getFilesInDir(FOLDER_EXPORT_ASSEMBLY)
    
    # if singleInstruction:
    #     singleInstructionTests, testcases, instrCount = stack.createSingleInstructionTest(random_ops, immediateProbability,
    #                                                                                       switchProbability,
    #                                                                                       singleInstruction)
    #     numberTestInstructions += testcases
    #     totalInstructions += instrCount
    #     for [instructionName, code] in singleInstructionTests:
    #         filestring = "singleInstr_" + instructionName + "_switch_" + str(
    #             int(switchProbability * 100)) +"_"+ runID+ "." + Processor().get_assembler_ending()
    #         exportFile = os.path.join(FOLDER_EXPORT_ASSEMBLY, filestring)
    #         rawfile = open(exportFile, 'w')

    #         rawfile.write(header)
    #         rawfile.write(code)
    #         rawfile.write(footer)
    #         rawfile.close()

    #         fileCount += 1
    #         exit(0)
    #         # count_instructions(exportFile, PATH_RISC_V, RESULT_FILE)
    temp_res = []

    if args.basicInstruction:
        
        if args.threads > 1:
            with multiprocessing.Pool(int(args.threads)) as pool:
                temp_res.extend(pool.starmap(create_basic_instruciton_test, [(runID, i, args) for i in range(files)]))
        else:
            for i in range(files):
                temp_res.append(create_basic_instruciton_test(runID, i, args))
        
       
    
    
    if args.completeInstruction:
        if args.threads > 1:
            with multiprocessing.Pool(int(args.threads)) as pool:
                temp_res.extend(pool.starmap(create_basic_instruciton_test, [(runID, i, args) for i in range(files)]))
        else:
            for i in range(files):
                temp_res.append(create_basic_instruciton_test(runID, i, args))
        

    if args.sequence:
        if args.threads > 1:
            with multiprocessing.Pool(int(args.threads)) as pool:
                temp_res.extend(pool.starmap(createSequence, [(runID, i, args) for i in range(files)]))
        else:
            for i in range(files):
                temp_res.append(createSequence(runID, i, args))

        

    if args.interleaving:
        if args.threads > 1:
            with multiprocessing.Pool(int(args.threads)) as pool:
                temp_res.extend(pool.starmap(createInterleaving, [(runID, i, args) for i in range(files)]))
        else:
            for i in range(files):
                temp_res.append(createInterleaving(runID, i, args))
        
           
            # count_instructions(exportFile, PATH_RISC_V, RESULT_FILE)

    # totalInstructions = 0
    # with open(RESULT_FILE, "r") as f:
    #     lines = f.readlines()
    #     for line in lines:
    #         totalInstructions += int(line.split()[-1])
    
    for res in temp_res:
        numberTestInstructions += res[0]
        totalInstructions += res[1]
        fileCount += res[2]


    print(f"Test Files generated        : {fileCount}")
    print("Test Instructions executed   : " + str(numberTestInstructions))
    print("Total Instructions Generated : " + str(totalInstructions))
    print("--- %s seconds ---" % (time.time() - start_time))
