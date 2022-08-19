# Copyright (c) 2022 Chair for Chip Design for Embedded Computing,
#                    Technische Universitaet Braunschweig, Germany
#                    www.tu-braunschweig.de/en/eis
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
import os
import subprocess
from os.path import exists, isdir

from Constants import FOLDER_EXPORT_ASSEMBLY
from util.Stack import Stack
import argparse

from util.ConditionalExecutionCode import ConditionalExecutionCode


def existsDirectory(path):
    if exists(path):
        return isdir(path)
    else:
        return False

def createDirectoryIfNew(directory):
    if not exists(directory):
        command = "mkdir -p " + directory
        subprocess.run(command, shell=True)





if __name__ == '__main__':
    v = ConditionalExecutionCode()
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version",
                        help="\n -1  =  single Instruction Test (only one Configuration per Instruction) \n-2  =  single Instruction Test (going through SIMD and signage options)\n0  = single Test (only one Configuration per Instruction and one File per instruction), 1 = interleaving Test, -1 = Instruction debugging. Defaults to 0.",
                        default="0")
    parser.add_argument("-l", "--level",
                        help="Number of level for the assembly. Defaults to 1.",
                        default="1")
    parser.add_argument("-i", "--immediate",
                        help="Probability of immediate generated. Range from 0.0 - 1.0. Defaults to 0.0.",
                        default="0.0")
    parser.add_argument("-f", "--files",
                        help="Number of assembly files created. Defaults to 5.",
                        default="5")
    parser.add_argument("-s", "--singleInstruction",
                        help="Test Single Instruction",
                        default="")
    args = parser.parse_args()
    version = int(args.version)
    depth = int(args.level)
    immediateProbability = float(args.immediate)
    files = int(args.files)
    singleInstruction = args.singleInstruction
    stack = Stack()
    # while True:
    #     version = int(input("v1 oder v2? 0: v1\t1: v2\n"))
    #     if version == 0 or version == 1:
    #         break
    #     print("Eingabe entw. 0 oder 1.")
    #     continue
    n=3

    #while True:
    #    tiefe = int(input("Bitte die Tiefe eingeben (int):\n"))
    #    break

    #while True:
    #    probability = float(input("Bitte die Wahrscheinlichkeit für Immediate eingeben (float zw. 0-1):\n"))
    #    if probability > 1.0 or probability < 0.0:
    #        print("Wert muss zw 0-1 liegen.")
    #        continue
    #    break

    # prepare Export folder
    createDirectoryIfNew(FOLDER_EXPORT_ASSEMBLY)

    instructionCount = 0


    if version ==-1:

        singleInstructionTests = stack.createSingleInstructionTest(singleInstruction=singleInstruction, immediateProbability=immediateProbability)
        for [instructionName, code] in singleInstructionTests:
            filestring = "assembly_"+instructionName+".asm"
            exportFile = os.path.join(FOLDER_EXPORT_ASSEMBLY, filestring)
            rawfile = open(exportFile, 'w+')
            header = open('header.txt', 'r')
            footer = open('footer.txt', 'r')
            rawfile.write(code)
            rawfile.close()
            with open(exportFile, 'r') as original: data = original.read()
            with open(exportFile, 'w') as modified: modified.write(header.read() + data)
            with open(exportFile, 'a') as modified: modified.write(footer.read())


    elif version == -2:

        singleInstructionTests = stack.createCompleteSingleInstructionTest(singleInstruction=singleInstruction, immediateProbability=immediateProbability)
        for [instructionName, code] in singleInstructionTests:
            filestring = "assembly_"+instructionName+".asm"
            exportFile = os.path.join(FOLDER_EXPORT_ASSEMBLY, filestring)
            rawfile = open(exportFile, 'w+')
            header = open('header.txt', 'r')
            footer = open('footer.txt', 'r')
            rawfile.write(code)
            rawfile.close()
            with open(exportFile, 'r') as original: data = original.read()
            with open(exportFile, 'w') as modified: modified.write(header.read() + data)
            with open(exportFile, 'a') as modified: modified.write(footer.read())
            n=3




    else:


        for i in range(files):
            filestring = 'assembly_{}.asm'.format(str(i))
            exportFile = os.path.join(FOLDER_EXPORT_ASSEMBLY,filestring)
            rawfile = open(exportFile, 'w+')
            header = open('header.txt', 'r')
            footer = open('footer.txt', 'r')




            if version == 0:
                code_v1 = stack.create_singleInstructions(depth, immediateProbability)
                rawfile.write(code_v1)

            elif version == 1:
                code,instrCount = stack.create_interleavingInstructions(depth, immediateProbability)
                code_v2 = code
                instructionCount += instrCount
                rawfile.write(code_v2)

            rawfile.close()
            with open(exportFile, 'r') as original: data = original.read()
            with open(exportFile, 'w') as modified: modified.write(header.read() + data)
            with open(exportFile, 'a') as modified: modified.write(footer.read())

    print(str(files) +" Assembly Files successfully generated.")
    print(str(instructionCount) + " number of instructions.")