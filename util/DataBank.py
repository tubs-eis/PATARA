# Copyright (c) 2022 Chair for Chip Design for Embedded Computing,
#                    Technische Universitaet Braunschweig, Germany
#                    www.tu-braunschweig.de/en/eis
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
import copy
import csv
import os, glob
from typing import List

import xmltodict

import Constants
from Constants import *
from util.Instruction import Instruction
from util.Processor import Processor
from util.TestInstruction import TestInstruction

class DataBank:
    class __Databank:
        def __init__(self):
            self._dict = {}
            self._readImmediateAssembly()
            self.read_xml()
            self._read_comparison_xml()
            self._read_init_register()
            self._readPostInit()
            n=3

        def _isInstruction(self, instr):
            if instr == COMPARISON:
                return False
            if instr == INSTRUCTION_DEFAULT_MODES:
                return False
            if instr == INIT:
                return False
            if instr == POST_INIT:
                return False
            if instr == IMMEDIATE_ASSEMBLY:
                return False
            if instr == CONDITIONAL_READ:
                return False

            return True

        def __parseInstructions(self, dictInstruction):
            result = []
            instructions = dictInstruction
            if not isinstance(dictInstruction, list):
                instructions = [dictInstruction]
            # instructions = [dictInstruction] if isinstance(dictInstruction, str) else dictInstruction
            for instr in instructions:
                i = Instruction(instr)

                mandatoryFeatures = {IMMEDIATE: IMMEDIATE_LONG}
                if isinstance(instr, dict):
                    if instr[MANDATORY_FEATURE]:
                        mandatoryFeatures = {}
                        for key, value in instr[MANDATORY_FEATURE].items():
                            mandatoryFeatures[key] = Processor().getProcessorFeatureList(key)[value]


                i.setGlobalMandatoryFeatures(mandatoryFeatures)
                result.append(i)
            return result


        def _readImmediateAssembly(self):
            self.immediateAssembly = None
            file = open(Constants.PATH_INSTRUCTION)
            xml_content = xmltodict.parse(file.read())

            for group in xml_content[INST_LIST]:
                if group == IMMEDIATE_ASSEMBLY:
                    immidateVariants = xml_content[INST_LIST][IMMEDIATE_ASSEMBLY]
                    self.immediateAssembly = {}
                    for imm in immidateVariants:
                        assemlby = Processor().getProcessorFeatureAssembly(IMMEDIATE, imm)
                        self.immediateAssembly[assemlby] = {}

                        if INSTR in xml_content[INST_LIST][IMMEDIATE_ASSEMBLY][imm]:
                            instr = xml_content[INST_LIST][IMMEDIATE_ASSEMBLY][imm][INSTR]
                            instructions = self.__parseInstructions(instr)
                            self.immediateAssembly[assemlby][vMutable] = instructions

                        else:
                            for simd in xml_content[INST_LIST][IMMEDIATE_ASSEMBLY][imm]:
                                instr = xml_content[INST_LIST][IMMEDIATE_ASSEMBLY][imm][simd][INSTR]
                                instructions = self.__parseInstructions(instr)

                                self.immediateAssembly[assemlby][simd] = instructions

                        # instruction = [instr] if isinstance(instr, str) else instr
                        # for instr in instruction:
                        #     i = Instruction_v1(instr)
                        #     i.setGlobalMandatoryFeatures({IMMEDIATE: IMMEDIATE_LONG})
                        #     self.immediateAssembly[assemlby].append(i)
            n=3



        def read_xml(self):
            file = open(Constants.PATH_INSTRUCTION)
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
                reverse = self._extractReverseSIMD(temp)
                specialization = {}
                if SPECIALIZATION in self.xml_content[INST_LIST][instr]:
                    specialization = self.xml_content[INST_LIST][instr][SPECIALIZATION]


                testInstruction = TestInstruction(original, reverse, instr, specialization, self.instructionList, copy.deepcopy(self.immediateAssembly))
                self.testinstruction_list.append(testInstruction)

            file.close()

        def _addDictEntry(self, instr):
            self._dict[instr] = copy.deepcopy(self.xml_content[INST_LIST][instr])
            del self._dict[instr][INSTR]
            del self._dict[instr][REVERSE]

        def _extractReverseSIMD(self, temp):
            reverse = temp[REVERSE]
            reverseDict = {}
            if isinstance(reverse, dict):
                simdVersions = Processor().getSIMD()
                for (simdKey, simdValue) in simdVersions.items():
                    if simdKey in reverse:
                        reverseDict[simdValue] = [reverse[simdKey][REVERSE]] if isinstance(reverse[simdKey][REVERSE],
                                                                                           str) else reverse[simdKey][
                            REVERSE]
            else:
                reverseList = [reverse] if isinstance(reverse, str) else reverse
                reverseDict[vMutable] = reverseList
            return reverseDict

        def _read_comparison_xml(self) -> list:
            """Reads xml to parse the comparison code."""
            file = open(Constants.PATH_INSTRUCTION)
            parser = xmltodict.parse(file.read())
            return_list = parser[INST_LIST][COMPARISON][INSTR]

            self._comparisonCode = return_list

        def _read_init_register(self) -> list:
            file = open(Constants.PATH_INSTRUCTION)
            parser = xmltodict.parse(file.read())
            return_list = parser[INST_LIST][INIT][REGISTER]

            # guarantee a list
            if not isinstance(return_list, list):
                return_list = [return_list]
            self._listInitRegister = return_list

        def _readPostInit(self):
            file = open(Constants.PATH_INSTRUCTION)
            parser = xmltodict.parse(file.read())
            return_list = parser[INST_LIST][POST_INIT][INSTR]

            self._listPostInit = return_list



    instance = None
    def __init__(self):
        if not DataBank.instance:
            DataBank.instance = DataBank.__Databank()


    def printdatabase(self):
        for k, v in self.instance._dict.items():
            print("-------------- %s" % (k))
            print(v)
            print(Processor().getAvailableInstructionFeatures(k))
            # find TestInstruction
            for testInstr in self.instance.testinstruction_list:
                if k == testInstr.getInstruction():
                    # print Instructions
                    for instruction in testInstr.getAssemblyInstructions():
                        print(instruction.getRawString())
                    print()
                    for simdVariant in testInstr.getReversiAssemblyInstructions():
                        print("SIMD: " ,simdVariant)
                        for instruction in testInstr.getReversiAssemblyInstructions()[simdVariant]:
                            print(instruction.getRawString())
                    print("\n\n")





    def getTestInstructions(self) -> List[TestInstruction]:
        return self.instance.testinstruction_list

    def getComparisonCode(self):
        return self.instance._comparisonCode

    def getInitRegister(self):
        return self.instance._listInitRegister

    def getSpecificTestInstruction(self, testInstructionName):
        for testInstruction in self.instance.testinstruction_list:
            if testInstruction.getInstruction() == testInstructionName:
                return testInstruction
        return None

    def getPostInitCode(self):
        return self.instance._listPostInit
