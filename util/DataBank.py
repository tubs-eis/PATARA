# Copyright (c) 2023 Chair for Chip Design for Embedded Computing,
#                    Technische Universitaet Braunschweig, Germany
#                    www.tu-braunschweig.de/en/eis
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


import copy
import random
from typing import List

import xmltodict

from Constants import *
from util.Instruction import Instruction
from util.Processor import Processor
from util.TestInstruction import TestInstruction


class DataBank:
    class __Databank:
        def __init__(self, architecture):
            self.architecture = architecture
            self._dict = {}
            self.ICacheMissInstruction = []
            self._readImmediateAssembly()
            self.read_xml()
            self._read_comparison_xml()
            self._read_init_register()
            self._readPostInit()
            self._readGlobalPreSequence()
            self._readFixedImmediate()
            self._readRandomizeProcessorState()

            n = 3

        def _isInstruction(self, key):
            if key == COMPARISON:
                return False
            if key == INSTRUCTION_DEFAULT_MODES:
                return False
            if key == INIT:
                return False
            if key == POST_INIT:
                return False
            if key == IMMEDIATE_ASSEMBLY:
                return False
            if key == CONDITIONAL_READ:
                return False
            if key == END_SIMULATION:
                return False
            if key == GLOBAL_PRE_SEQUENCE:
                return False
            if key == FIX_IMM_VALUE:
                return False
            if key == PRE_REVERSE_PROCESSOR_STATE:
                return False
            if key == PRE_REVERSE_POST_REG_INIT_PROCESSOR_STATE:
                return False
            if key == POST_REVERSE_PROCESSOR_STATE:
                return False

            return True

        def __parseInstructions(self, dictInstruction):
            result = []
            instructions = dictInstruction
            if not isinstance(dictInstruction, list):
                instructions = [dictInstruction]
            for instr in instructions:
                i = Instruction(instr)

                mandatoryFeatures = {IMMEDIATE: Processor().getImmediateDefault()}
                if isinstance(instr, dict):
                    if instr[MANDATORY_FEATURE]:
                        mandatoryFeatures = {}
                        for key, value in instr[MANDATORY_FEATURE].items():
                            mandatoryFeatures[key] = value
                i.setGlobalMandatoryFeatures(mandatoryFeatures)
                result.append(i)
            return result

        def _readImmediateAssembly(self):
            self.immediateAssembly = None
            file = open(get_path_instruction(self.architecture))
            xml_content = xmltodict.parse(file.read())

            for group in xml_content[INST_LIST]:
                if group == IMMEDIATE_ASSEMBLY:
                    immidateVariants = xml_content[INST_LIST][IMMEDIATE_ASSEMBLY]
                    self.immediateAssembly = {}
                    for imm in immidateVariants or []:
                        self.immediateAssembly[imm] = {}
                        if INSTR in xml_content[INST_LIST][IMMEDIATE_ASSEMBLY][imm]:
                            instr = xml_content[INST_LIST][IMMEDIATE_ASSEMBLY][imm][INSTR]
                            instructions = self.__parseInstructions(instr)
                            self.immediateAssembly[imm][V_MUTABLE] = instructions
                        else:
                            for simd in xml_content[INST_LIST][IMMEDIATE_ASSEMBLY][imm]:
                                instr = xml_content[INST_LIST][IMMEDIATE_ASSEMBLY][imm][simd][INSTR]
                                instructions = self.__parseInstructions(instr)
                                self.immediateAssembly[imm][simd] = instructions

        def read_xml(self):
            file = open(get_path_instruction(self.architecture))
            self.xml_content = xmltodict.parse(file.read())
            self.testinstruction_list = []
            self.instructionList = []
            # generate Characteristics Dictionary about Instructions
            for instr in self.xml_content[INST_LIST]:
                if not self._isInstruction(instr):
                    continue

                self._addDictEntry(instr)
                self.instructionList.append(instr)

            # generate TestInstructions
            for instr in self.xml_content[INST_LIST]:
                if not self._isInstruction(instr):
                    continue

                temp = self.xml_content[INST_LIST][instr]
                original = temp[INSTR]
                original = [original] if isinstance(original, str) else original
                if PRE_SEQUENCE_INSTR in temp:
                    preSequence = temp[PRE_SEQUENCE_INSTR]
                    preSequence = [preSequence] if isinstance(preSequence, str) else preSequence
                else:
                    preSequence = []

                if SEQUENCE_INSTR in temp:
                    sequence = temp[SEQUENCE_INSTR]
                    sequence = [sequence] if isinstance(sequence, str) else sequence
                else:
                    sequence = []

                iCacheRepetition = []
                if SEQUENCE_INSTR_CACHE_REPETITION in temp:
                    iCacheRepetition = temp[SEQUENCE_INSTR_CACHE_REPETITION]
                    iCacheRepetition = [iCacheRepetition] if isinstance(iCacheRepetition, str) else iCacheRepetition

                if POST_SEQUENCE_INSTR in temp:
                    postSequence = temp[POST_SEQUENCE_INSTR]
                    postSequence = [postSequence] if isinstance(postSequence, str) else postSequence
                else:
                    postSequence = []
                reverse = self._extractReverseSIMD(temp)
                specialization = {}
                if SPECIALIZATION in self.xml_content[INST_LIST][instr]:
                    specialization = self.xml_content[INST_LIST][instr][SPECIALIZATION]

                instrType = self._getInstructionType(temp)
                intImms = self._getSpecialImmediates(temp)
                icacheMissCandidate = self._getICacheMissCandidate(temp)

                testInstruction = TestInstruction(original, preSequence, sequence, postSequence, reverse, instr,
                                                  specialization,
                                                  self.instructionList, copy.deepcopy(self.immediateAssembly),
                                                  instrType, specialImmediates=intImms,
                                                  icacheMissCandidate=icacheMissCandidate,
                                                  iCacheRepetition=iCacheRepetition)
                self.testinstruction_list.append(testInstruction)
                if testInstruction.isImemCacheMissCandidate():
                    temp = copy.deepcopy(testInstruction)
                    temp.setICacheJump()
                    self.ICacheMissInstruction.append(temp)

            file.close()

        def _getInstructionType(self, temp):
            type = ""
            if INSTRUCTION_TYPE in temp:
                type = temp[INSTRUCTION_TYPE]
            return type

        def _getSpecialImmediates(self, temp):
            intImms = []
            if SPECIAL_IMMEDIATES in temp:
                immediates = temp[SPECIAL_IMMEDIATES]
                immList = immediates.split(INTEGER_DELIMITER)
                intImms = []
                for i in immList:
                    intImms.append(int(i))
            return intImms

        def _getICacheMissCandidate(self, temp):
            return I_CACHE_MISS_CANDIDATE in temp

        def getICacheMissTestInstruction(self):
            return copy.deepcopy(random.choice(self.ICacheMissInstruction))

        def _readFixedImmediate(self):
            if FIX_IMM_VALUE in self.xml_content[INST_LIST]:
                fixedInstructions = self.xml_content[INST_LIST][FIX_IMM_VALUE][INSTR]
                if isinstance(fixedInstructions, str):
                    fixedInstructions = [fixedInstructions]

                self.fixedInstructions: List[Instruction] = []
                for instr in fixedInstructions:
                    self.fixedInstructions.append(Instruction(instr))

        def _readRandomizeProcessorState(self):
            self.preReverseProcessorState = self.__importSpecialInstructions(PRE_REVERSE_PROCESSOR_STATE)
            self._setRandomImmediateType()
            self.preReversePostRegInitProcessorState = self.__importSpecialInstructions(
                PRE_REVERSE_POST_REG_INIT_PROCESSOR_STATE)
            self.postReverseProcessorState = self.__importSpecialInstructions(POST_REVERSE_PROCESSOR_STATE)

        def _setRandomImmediateType(self):
            self.randomImmediateType = None
            randomImmediate = OPERANDS.RAND_IMMEDIATE1.value
            for instr in self.preReverseProcessorState:
                if randomImmediate in instr.string():
                    self.randomImmediateType = instr.getFeatures()[OPERAND_TYPE.IMMEDIATE.value]
                    return

        def __importSpecialInstructions(self, keyword):
            liste = []
            if keyword in self.xml_content[INST_LIST]:
                for instr in self.xml_content[INST_LIST][keyword][INSTR]:
                    instruction = Instruction(instr)
                    liste.append(instruction)
            return liste

        def _addDictEntry(self, instr):
            self._dict[instr] = copy.deepcopy(self.xml_content[INST_LIST][instr])
            del self._dict[instr][INSTR]
            del self._dict[instr][REVERSE]
            if SEQUENCE_INSTR in self._dict[instr]:
                del self._dict[instr][SEQUENCE_INSTR]

        def _extractReverseSIMD(self, temp):
            reverse = temp[REVERSE]
            reverseDict = {}
            if isinstance(reverse, dict):
                simdVersions = Processor().getSIMD()
                for (simdKey, simdValue) in simdVersions.items():
                    if simdKey in reverse:
                        reverseDict[simdKey] = [reverse[simdKey][REVERSE]] if isinstance(reverse[simdKey][REVERSE],
                                                                                         str) else reverse[simdKey][
                            REVERSE]
            else:
                reverseList = [reverse] if isinstance(reverse, str) else reverse
                reverseDict[V_MUTABLE] = reverseList
            return reverseDict

        def _read_comparison_xml(self) -> list:
            """Reads xml to parse the comparison code."""
            file = open(get_path_instruction(self.architecture))
            parser = xmltodict.parse(file.read())
            return_list = parser[INST_LIST][COMPARISON][INSTR]

            self._comparisonCode = return_list

        def _readGlobalPreSequence(self) -> list:
            """Reads xml to parse the GlobalPrePlain code."""
            file = open(get_path_instruction(self.architecture))
            parser = xmltodict.parse(file.read())

            return_list = []
            if GLOBAL_PRE_SEQUENCE in parser[INST_LIST]:
                if isinstance(parser[INST_LIST][GLOBAL_PRE_SEQUENCE][INSTR], list):
                    return_list = parser[INST_LIST][GLOBAL_PRE_SEQUENCE][INSTR]
                else:
                    return_list = [parser[INST_LIST][GLOBAL_PRE_SEQUENCE][INSTR]]

            self._globalPrePlain = return_list

        def _read_init_register(self) -> list:
            file = open(get_path_instruction(self.architecture))
            parser = xmltodict.parse(file.read())
            return_list = parser[INST_LIST][INIT][REGISTER]

            # guarantee a list
            if not isinstance(return_list, list):
                return_list = [return_list]
            self._listInitRegister = return_list

        def _readPostInit(self):
            self._listPostInit = {}

            file = open(get_path_instruction(self.architecture))
            parser = xmltodict.parse(file.read())
            if POST_INIT in parser[INST_LIST]:
                return_list = parser[INST_LIST][POST_INIT][INSTR]
                self._listPostInit = return_list

        def getFixedImmediateCode(self, operands, immediate):
            code = ""
            instrCount = 0
            for instr in self.fixedInstructions:
                i = copy.deepcopy(instr)
                operands = copy.deepcopy(operands)
                i.enableRandValueRandomImmediate()
                operands[OPERANDS.RAND_IMMEDIATE.value] = str(immediate)
                i.setOperands(operands)
                code += i.string() + "\n"
                instrCount += 1
            return code, instrCount

        def getFixedImmediateInstructionCount(self):
            instrCount = 0
            for instr in self.fixedInstructions:
                instrCount += 1
            return instrCount

    instance = None

    def __init__(self, architecture="rv32imc"):
        if not DataBank.instance:
            DataBank.instance = DataBank.__Databank(architecture)

    def getTestInstructions(self) -> List[TestInstruction]:
        return self.instance.testinstruction_list

    def getComparisonCode(self):
        return self.instance._comparisonCode

    def getGlobalPreSequenceCode(self):
        return self.instance._globalPrePlain

    def getInitRegister(self):
        return self.instance._listInitRegister

    def getPostInitCode(self):
        return self.instance._listPostInit

    def getInstruction(self, instructionName):
        for instr in self.instance.testinstruction_list:
            if instr.instruction == instructionName:
                return instr

        return None

    def getFixedImmediateCode(self, operands, immediate):
        return self.instance.getFixedImmediateCode(operands, immediate)

    def getFixedImmediateInstructionCount(self):
        return self.instance.getFixedImmediateInstructionCount()

    def getICacheMissTestInstruction(self):
        return self.instance.getICacheMissTestInstruction()

    def assemblyRandomizeRegisterFile(self):
        immediateType = Processor().getImmediateDefault()
        self.initRegCounter = 0
        # Initialize all Registers with random value

        reg_rule = Processor().get_register_rule()
        max_reg_file = reg_rule[NUM_REG_FILES]
        max_reg_size = reg_rule[REG_FILE_SIZE]

        init_csv = self.getInitRegister()
        IgnoredRegister = Processor().getIgnoreRegister()

        code = ''
        for bank in range(max_reg_file + 1):
            for register in range(max_reg_size + 1):
                if [bank, register] in IgnoredRegister:  # Don't initialize ignored registers
                    continue
                reg_operand = Processor().createRegisterOperand(bank, register)
                for instr in init_csv:
                    immediate = Processor().createRandImmediate(
                        instr[MANDATORY_FEATURE][IMMEDIATE] if isinstance(instr, dict) and instr[MANDATORY_FEATURE][
                            IMMEDIATE] else immediateType)
                    instr = instr[PLACEHOLDER] if isinstance(instr, dict) else instr
                    instr = instr.replace(OPERANDS.TARGET_REGISTER.value, reg_operand)
                    instr = instr.replace(OPERANDS.RAND_VALUE.value, immediate)
                    code += str(instr)
                    code += '\n'

        code += "\n"
        if isinstance(self.getPostInitCode(), str):
            postInit = self.getPostInitCode()
        else:
            postInit = "\n".join(self.getPostInitCode())

        if OPERANDS.BRANCH_INDEX.value in postInit:
            postInit = postInit.replace(OPERANDS.BRANCH_INDEX.value, str(self.initRegCounter))
        code += postInit
        code += "\n"
        code += "\n"
        self.initRegCounter += 1
        return code

    def randomizeProcessorState(self, testInstructionOperands, enabledFeatures):
        if len(self.instance.preReverseProcessorState) == 0:
            return ""

        operands = Processor().generateRandomOperands(enabledFeatures, generateFocusRegister=False,
                                                      randImmediateExtension=self.instance.randomImmediateType)
        operands[OPERANDS.FOCUS_REGISTER.value] = testInstructionOperands[OPERANDS.FOCUS_REGISTER.value]
        operands[OPERANDS.TARGET_REGISTER.value] = testInstructionOperands[OPERANDS.TARGET_REGISTER.value]
        operands[OPERANDS.RAND_VALUE.value] = testInstructionOperands[OPERANDS.RAND_VALUE.value]
        code = ""
        code += "\n" + Processor().get_assembler_comment() + " randomizing Processor States and Register File\n"
        n = 0
        for instr in self.instance.preReverseProcessorState:
            instr.setOperands(operands)
            code += instr.string() + "\n"
            n += 1
        # randomize register file
        code += self.assemblyRandomizeRegisterFile()
        for instr in self.instance.preReversePostRegInitProcessorState:
            instr.setOperands(operands)
            code += instr.string() + "\n"

        return code

    def restoreRandomizedFocusRegister(self, testInstructionOperands, enabledFeatures):
        operands = Processor().generateRandomOperands(enabledFeatures, generateFocusRegister=False,
                                                      randImmediateExtension=self.instance.randomImmediateType)
        operands[OPERANDS.FOCUS_REGISTER.value] = testInstructionOperands[OPERANDS.FOCUS_REGISTER.value]
        code = ""
        n = 0
        for instr in self.instance.postReverseProcessorState:
            instr.setOperands(operands)
            code += instr.string() + "\n"
            n += 1
        return code
