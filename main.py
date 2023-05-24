import argparse
import os
import subprocess
import time
from os.path import exists, isdir

from Constants import FOLDER_EXPORT_ASSEMBLY, get_path_header, get_path_footer
from util.ConditionalExecutionCode import ConditionalExecutionCode
from util.Processor import Processor
from util.Stack import Stack


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


if __name__ == '__main__':
    start_time = time.time()
    parser = argparse.ArgumentParser()

    required = parser.add_argument_group('Program Modes')
    required.add_argument("-b", "--singleInstruction",
                          help="Test Single Instruction. In combination with complete instruciton, will only generate all variants for this single instruction.",
                          default="")
    required.add_argument("--basicInstruction",
                          help="Instructions for all basic instructions, don't execute special case code.",
                          action="store_true")
    required.add_argument("-c", "--completeInstruction",
                          help="complete single Instruction Test (going through every possible option one file per instruction)",
                          action="store_true")
    required.add_argument("-i", "--interleaving", help="interleaving Test.", action="store_true")
    required.add_argument("-s", "--sequence",
                          help="if set an extra instruction path with only plain instructions gets created and compares it results with the normal instruction path.",
                          action="store_true")

    optional = parser.add_argument_group('optional arguments')
    optional.add_argument("-a", "--architecture",
                          help="Architecture description folder in sources/ARCHITECTURE. Defaults to rv32imc.",
                          default="rv32imc")
    optional.add_argument("-l", "--level", help="Number of interleaving stacks in sequence. Defaults to 1.",
                          default="1")
    optional.add_argument("--immediate",
                          help="Probability of immediate generated. Range from 0.0 - 1.0. Defaults to 0.5.",
                          default="0.5")
    optional.add_argument("--switch",
                          help="Probability of instructions with switched focusReg and randValue generated. Range from 0.0 - 1.0. Defaults to 0.5.",
                          default="0.5")
    optional.add_argument("-r", "--repetitions", help="Repetitions of complex tests to create. Defaults to 1.",
                          default="1")
    optional.add_argument("--simulator", help="modify for simulation", action="store_true")
    optional.add_argument("-f", "--forwarding",
                          help="Test Sequence with FORWARDING instruction inside of the sequence. Defaults to 0.",
                          default=0)
    optional.add_argument("--specialImmediates", help="Create Sequences which test Special immediates. Defaults to 0.",
                          default="0.0")
    optional.add_argument("--newMemoryBlock",
                          help="Probability of starting a new memory block region. Defaults to 0.0.", default="0.0")
    optional.add_argument("--dcacheMiss", help="Probability of incuring Data Cache misses. Defaults to 0.5.",
                          default="0.5")
    optional.add_argument("--icacheMiss",
                          help="Probability of incuring Instruction Cache miss. Defaults to 0.5. Not supported on sequences!",
                          default="0.5")
    optional.add_argument("--sequenceLength",
                          help="Give the list of Sequences to iterate through. Defaults to 4. Only works on sequences!",
                          default=4)
    optional.add_argument("--sequenceStall",
                          help="Probability to stall the pipeline between base instructions with forwarding holes. Defaults to 0.5",
                          default=0.5)



    args = parser.parse_args()

    dCacheMisses = float(args.dcacheMiss)
    newMemoryBlock = float(args.newMemoryBlock)

    Processor(architecture=args.architecture, cacheMiss=float(dCacheMisses),
              newMemoryBlock=float(newMemoryBlock))

    sequenceLength = int(args.sequenceLength)

    switchProbability = float(args.switch)
    depth = int(args.level)
    useSimulator = args.simulator
    immediateProbability = float(args.immediate)
    files = int(args.repetitions)
    singleInstruction = args.singleInstruction
    stack = Stack(args.architecture, args.icacheMiss)
    v = ConditionalExecutionCode(args.architecture)
    # prepare Export folder
    createDirectoryIfNew(FOLDER_EXPORT_ASSEMBLY)
    forwardingHole = int(args.forwarding)
    specialImmediates = float(args.specialImmediates)
    forwardingStallProb = float(args.sequenceStall)

    # import Constant files
    headerFile = open(get_path_header(args.architecture, simulator=useSimulator), 'r')
    header = headerFile.read()
    headerFile.close()
    footerFile = open(get_path_footer(args.architecture, simulator=useSimulator), 'r')
    footer = footerFile.read()
    footerFile.close()

    # liste = []
    # liste.append(copy.deepcopy(DataBank(args).getInstruction("sw")))
    # liste.append(copy.deepcopy(DataBank(args).getInstruction("rem")))
    # liste.append(copy.deepcopy(DataBank(args).getInstruction("lw")))
    # liste.append(copy.deepcopy(DataBank(args).getInstruction("sra")))
    #
    # code, testInstr, instrCount = stack.createSequenceInstructions(liste, immediateProbability=immediateProbability,
    #                                                                switchProbability=switchProbability, forwarding=0,
    #                                                                specialImmediates=specialImmediates)
    #
    # file = open(os.path.join(FOLDER_EXPORT_ASSEMBLY, "test.S"), "w")
    # file.write(header)
    # file.write(code)
    # file.write(footer)
    # file.close()
    # exit()
    runID = str(int(time.time()))
    numberTestInstructions = 0
    totalInstructions = 0
    fileCount =0
    original_fileCount = getFilesInDir(FOLDER_EXPORT_ASSEMBLY)

    if singleInstruction:
        singleInstructionTests, testcases, instrCount = stack.createSingleInstructionTest(immediateProbability,
                                                                                          switchProbability,
                                                                                          singleInstruction)
        numberTestInstructions += testcases
        totalInstructions += instrCount
        for [instructionName, code] in singleInstructionTests:
            filestring = "singleInstr_" + instructionName + "_switch_" + str(
                int(switchProbability * 100)) +"_"+ runID+ "." + Processor().get_assembler_ending()
            exportFile = os.path.join(FOLDER_EXPORT_ASSEMBLY, filestring)
            rawfile = open(exportFile, 'w')

            rawfile.write(header)
            rawfile.write(code)
            rawfile.write(footer)
            rawfile.close()

            fileCount += 1

    if args.basicInstruction:
        # for i in range(files):
        i = 0
        singleInstructionTests, testcases, instrCount = stack.createBasicSingleInstructionTest(singleInstruction)
        numberTestInstructions += testcases
        totalInstructions += instrCount
        for instructionName, code in singleInstructionTests.items():
            filestring = "basic_" + instructionName + "_" + str(i) +"_"+ runID+ "." + Processor().get_assembler_ending()
            exportFile = os.path.join(FOLDER_EXPORT_ASSEMBLY, filestring)

            rawfile = open(exportFile, 'w')
            rawfile.write(header)
            rawfile.write(code)
            rawfile.write(footer)
            rawfile.close()

            fileCount += 1

    if args.completeInstruction:

        # for i in range(files):
        i = 0
        singleInstructionTests, testcases, instrCount = stack.createCompleteSingleInstructionTest(singleInstruction)
        numberTestInstructions += testcases
        totalInstructions += instrCount
        for instructionName, code in singleInstructionTests.items():
            filestring = "complete_" + instructionName + "_" + str(i)+"_"+ runID + "." + Processor().get_assembler_ending()
            exportFile = os.path.join(FOLDER_EXPORT_ASSEMBLY, filestring)

            rawfile = open(exportFile, 'w')
            rawfile.write(header)
            rawfile.write(code)
            rawfile.write(footer)
            rawfile.close()

            fileCount += 1

    if args.sequence:

        for i in range(files):
            instructions = stack.generateSequenceInstructionsList(sequenceLength)
            for instructionList in instructions:
                code, testInstr, instrCount = stack.createSequenceInstructions(instructionList, immediateProbability,
                                                                               switchProbability, forwardingHole,
                                                                               specialImmediates,
                                                                               forwardingStallProb=forwardingStallProb)
                numberTestInstructions += testInstr
                totalInstructions += instrCount
                # export file
                filestring = "sequence"
                filestring += "_switch_" + str(int(switchProbability * 100))
                filestring += "_forwarding_" + str(forwardingHole)
                filestring += "_forwardStall_" + str(int(forwardingStallProb * 100))
                filestring += "_specialImms_" + str(int(specialImmediates * 100))
                filestring += "_dcache_" + str(int(dCacheMisses * 100))
                filestring += "_newMemBlock_" + str(int(newMemoryBlock * 100))
                filestring += "_" + str(i)
                filestring += "_" + str(fileCount)
                filestring += "_"+ runID
                filestring += "." + Processor().get_assembler_ending()
                exportFile = os.path.join(FOLDER_EXPORT_ASSEMBLY, filestring)

                rawfile = open(exportFile, 'w')
                rawfile.write(header)
                rawfile.write(code)
                rawfile.write(footer)
                rawfile.close()

                fileCount += 1

    if args.interleaving:
        for i in range(files):
            filestring = "interleaving"
            filestring += "_switch_" + str(int(switchProbability * 100))
            filestring += "_specialImms_" + str(int(specialImmediates * 100))
            filestring += "_dcache_" + str(int(dCacheMisses * 100))
            filestring += "_newMemBlock_" + str(int(newMemoryBlock * 100))
            filestring += "_" + str(i)
            filestring += "_" + str(fileCount)
            filestring += "_" + runID
            filestring += "." + Processor().get_assembler_ending()

            code, testInstr, instrCount = stack.createInterleavingInstructions(depth, immediateProbability,
                                                                               switchProbability,
                                                                               specialImmediates=specialImmediates)

            numberTestInstructions += testInstr
            totalInstructions += instrCount

            exportFile = os.path.join(FOLDER_EXPORT_ASSEMBLY, filestring)
            rawfile = open(exportFile, 'w')
            rawfile.write(header)
            rawfile.write(code)
            rawfile.write(footer)
            rawfile.close()

            fileCount += 1




    print(str(fileCount) + " Assembly Files successfully generated. Total files in folder: " + str(original_fileCount + fileCount))
    print("Test Instructions created: " + str(numberTestInstructions))
    print("--- %s seconds ---" % (time.time() - start_time))
