# Copyright (c) 2022 Chair for Chip Design for Embedded Computing,
#                    Technische Universitaet Braunschweig, Germany
#                    www.tu-braunschweig.de/en/eis
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
import random
import sys
import copy # for deepcopy
import warnings

from docutils.nodes import warning

from util.DataBank import DataBank
from util.Processor import Processor
from Constants import *
from random import choice



class Stack:

    def __init__(self):
        self.processor = Processor()
        self._TestInstructions = DataBank().getTestInstructions() # List of Instruction combos (TestInstruction)
        self._instructionsList = [] # List of Testinstr to run (randomized from _TestInstructions)
        self.max_level = int(self.processor.instance.register[REG_FILE_SIZE])-2 # Num registers - 2
        self.initRegCounter = 0


    def generate_instructions_list(self, level: int, singleInstruction=""):
        self._instructionsList = []
        if singleInstruction != "":
            for testInstruction in self._TestInstructions:
                if testInstruction.getInstruction() == singleInstruction:
                    self._instructionsList.append(testInstruction)
                    return

        # warnings.warn("Stack::Generate_Instructions_list is limited to 2")
        # # self._instructionsList = [self._TestInstructions[9], self._TestInstructions[17], self._TestInstructions[15]]
        # self._instructionsList = [self._TestInstructions[16], self._TestInstructions[11], self._TestInstructions[2], self._TestInstructions[5], self._TestInstructions[17], self._TestInstructions[15]]
        # self._instructionsList = [self._TestInstructions[16], self._TestInstructions[11], self._TestInstructions[2], self._TestInstructions[5], self._TestInstructions[15]]
        # self._instructionsList = [ self._TestInstructions[17], self._TestInstructions[16]]
        # self._instructionsList = [self._TestInstructions[16], self._TestInstructions[11], self._TestInstructions[2], self._TestInstructions[5], self._TestInstructions[17], self._TestInstructions[15]]
        # # self._instructionsList = [self._TestInstructions[0], self._TestInstructions[10], self._TestInstructions[11], self._TestInstructions[15]]
        # return
        if level <= self.max_level:

            for i in range(level):
                # deep copy elements, because in the instructionlist they are changed.
                # This should not affect all occurences inside the instructionslist
                random.shuffle(self._TestInstructions)
                self._instructionsList.extend(copy.deepcopy(self._TestInstructions))
        else:
            sys.exit("ERROR: Level is more than max level. max level: {}".format(self.max_level))

    def chain_instruction(self, probability = 0):
        focus_register = None
        i =0
        for testInstruction in self._instructionsList:
            # print(str(i) + " : Focus: " + str(focus_register))
            testInstruction.set_random_features(probability)
            testInstruction.generateRandomOperands(focus_register)
            focus_register = testInstruction.getTargetOperand()
            i+=1

        # print(focus_register)
        for testInstruction in reversed(self._instructionsList):
            testInstruction.setTargetRegister(focus_register)



    def randomizeInstructionListFeatures(self, immediateProbability = 0):
        for testInstruction in self._instructionsList:
            testInstruction.set_random_features(immediateProbability)

    def generateRandomOperandsInstructionListFeatures(self):
        for testInstruction in self._instructionsList:
            testInstruction.generateRandomOperands(None)

    def get_instructions(self):
        code = ''
        # generate Code
        for instr in self._instructionsList:
            # print(instr.instruction)
            code += "\n//"+instr.getInstruction() +"\n"
            code += instr.generateCode()

        # generate Reversi
        for instr in reversed(self._instructionsList):
            # print(instr.instruction)
            code += "\n// REVERSE:" + instr.getInstruction() + "\n"
            code += instr.generateReversiCode()

        # generate comparison code
        code += self.generate_comparison_code(0,-1)

        # print(code)
        return code

    def getInstructionCount(self):
        instructionCount = 0
        for instr in self._instructionsList:
            try:
                instructionCount+= instr.getInstructionCount()
            except:
                n=3

        return instructionCount

    def getInstructionList(self):
        return self._instructionsList

    def getInstructionListString(self):
        string = ""
        for instr in self._instructionsList:
            string += instr.getInstruction()
            string+= "\n"
        return string

    def generate_comparison_code(self, focusInstructionNumber, targetInstructionNumber) -> str:
        """Generates the comparison code by reading it from the xml."""
        focusInstruction = self._instructionsList[focusInstructionNumber]
        targetInstruction = self._instructionsList[targetInstructionNumber]
        comparisionCode = DataBank().getComparisonCode()

        return self.processor.generate_ComparisonCode(comparisionCode, focusInstruction, targetInstruction)

    def init_registers(self) -> str:
        # Initialize all Registers with random value
        defaultFeatures = Processor().getAvailableInstructionFeatures()
        enabledfeatures = {IMMEDIATE: Processor().getAvailableInstructionFeatures()[IMMEDIATE].index(IMMEDIATE_LONG)}

        reg_rule = self.processor.get_register_rule()
        max_reg_file = int(reg_rule[NUM_REG_FILES])
        max_reg_size = int(reg_rule[REG_FILE_SIZE])

        init_csv = DataBank().getInitRegister()

        code = ''
        for bank in range(max_reg_file+1):
            for register in range(max_reg_size+1):
                reg_operand = self.processor.create_register_operand(bank, register)
                for instr in init_csv:
                    immediate = self.processor.createRandImmediate(IMMEDIATE_LONG)
                    instr = instr.replace(TARGET_REGISTER, reg_operand)
                    instr = instr.replace(RAND_VALUE, immediate)
                    code += str(instr)
                    code += '\n'

        code += "\n"
        if isinstance(DataBank().getPostInitCode(), str):
            postInit = DataBank().getPostInitCode()

            # code += DataBank().getPostInitCode()
        else:
            postInit = "\n".join(DataBank().getPostInitCode())
        if OPERANDS.BRANCH_INDEX.value in postInit:
            postInit = postInit.replace(OPERANDS.BRANCH_INDEX.value, str(self.initRegCounter))
        code += postInit
        code += "\n"
        code += "\n"
        self.initRegCounter += 1
        return code

    def _create_interleavingInstructions(self, level: int = 1, immediateProbability = 0):
        self.generate_instructions_list(level)
        self.chain_instruction(immediateProbability)
        code = self.get_instructions()
        instructionCount = self.getInstructionCount()
        # reset instr list
        self.resetInstructionList()
        return code, instructionCount

    def create_interleavingInstructions(self, level: int = 1, immediateProbability = 0):
        code = self.init_registers()  # Initialize rand value in register
        testCode, instructionCount = self._create_interleavingInstructions(level, immediateProbability)
        code += testCode
        # reset processor for next independent execution
        self.resetInstructionList()
        Processor().reset()
        return code,instructionCount

    def create_singleInstructions(self, level: int = 1, immediateProbability = 0):
        code = self.init_registers()
        self.generate_instructions_list(level)
        self.randomizeInstructionListFeatures(immediateProbability)
        self.generateRandomOperandsInstructionListFeatures()
        for index in range(len(self._instructionsList)):
            self._instructionsList[index].generateRandomOperands(None)
            code += self._instructionsList[index].generateCode()
            code += self._instructionsList[index].generateReversiCode()
            code += self.generate_comparison_code(index, index)
            Processor().reset()
        self.resetInstructionList()
        return code

    def resetInstructionList(self):
        self._instructionsList = []

    def createSingleInstructionTest(self, level=1, immediateProbability = 0, singleInstruction=""):
        result = []
        self.generate_instructions_list(level, singleInstruction)
        self.randomizeInstructionListFeatures(immediateProbability)
        for index in range(len(self._instructionsList)):
            testInstruction = self._instructionsList[index]
            v = Processor().getAvailableInstructionFeatures(testInstruction.getInstruction())
            testInstruction.generateRandomOperands()
            code = self.init_registers()
            code += testInstruction.generateCode()
            code += testInstruction.generateReversiCode()
            code += self.generate_comparison_code(index, index)
            Processor().reset()
            result.append([testInstruction.getInstruction(), code])

        return result


    def createCompleteSingleInstructionTest(self, immediateProbability =0, singleInstruction=""):
        """
        Test Signage and SIMD versions of each TestInstruction.
        :param immediateProbability:
        :return:
        """
        defaultFeatures = Processor().getAvailableInstructionFeatures()
        enabledfeatures = {
            IMMEDIATE: IMMEDIATE_LONG}








        result = []
        errors = []
        self.generate_instructions_list(1,  singleInstruction)
        self.randomizeInstructionListFeatures(immediateProbability)
        for index in range(len(self._instructionsList)):
            v = Processor().getAvailableInstructionFeatures(self._instructionsList[index].getInstruction())
            instrStr = self._instructionsList[index].getInstruction()
            testInstruction = self._instructionsList[index]



            for immidiateIndex in range(len(v[IMMEDIATE])):
                testInstruction.setEnableFeatureIndex(IMMEDIATE, immidiateIndex)
            # testInstruction.set_random_features(immediateProbability=immediateProbability)
            # testInstruction.setEnableFeatureIndex(CONDITIONAL, 0)
                for condition in range(len(v[CONDITIONAL])):
                    # value = v[CONDITIONAL][condition]
                    # featureValue = Processor().getAssemlby2Feature(value)
                    # if featureValue == "conditional-read":
                    #     testInstruction.setEn

                    testInstruction.setEnableFeatureIndex(CONDITIONAL, condition)
                    for flagCondSettings in ["carry", "overflow", "zero", "negative"]:
                        if condition ==1:
                            testInstruction.setEnableFeature(CONDITIONAL_READ, flagCondSettings)
                        for saturation in range(len(v[SATURATION])):
                            testInstruction.setEnableFeatureIndex(SATURATION, saturation)
                            for signage in range(len(v[SIGNAGE])):
                                testInstruction.setEnableFeatureIndex(SIGNAGE, signage)
                                for simdIndex in range(len(v[SIMD])):
                                    testInstruction.setEnableFeatureIndex(SIMD, simdIndex)


                                    code = self.init_registers()

                                    config = ""
                                    if testInstruction.getEnabledFeature(IMMEDIATE):
                                        config += "I"
                                    if condition >0 :
                                        config += "_"+testInstruction.getEnabledFeature(
                                        CONDITIONAL)+"_"+flagCondSettings +"_"
                                    else:
                                        config += "_"

                                    sign = testInstruction.getEnabledFeature(
                                        SIGNAGE)  # Processor().getFeature(SIGNAGE, signage, instrStr=instrStr)
                                    if not sign:
                                        sign = ""
                                    config +=  sign

                                    simdStr = testInstruction.getEnabledFeature(SIMD) #Processor().getFeature(SIMD, simdIndex, instrStr=instrStr)
                                    if not simdStr:
                                        simdStr = ""
                                    config += simdStr
                                    sat = testInstruction.getEnabledFeature(
                                        SATURATION)  # Processor().getFeature(SATURATION, saturation, instrStr=instrStr)
                                    if not sat:
                                        sat = ""
                                    config += sat

                                    testInstruction.generateRandomOperands()


                                    code += testInstruction.generateCode()
                                    code += testInstruction.generateReversiCode()
                                    code += self.generate_comparison_code(index, index)

                                    code += "\n\n"
                                    result.append([testInstruction.getInstruction() + config, code])
                                # except:
                                #     errors.append(testInstruction)
                                # finally:
                                    Processor().reset()



        return result


    def printSingleReversiCode(self, instructionName):
        testInstruction = DataBank().getSpecificTestInstruction(instructionName)
        testInstruction.set_random_features()
        print(testInstruction.generateCode())
        print(testInstruction.generateReversiCode())
