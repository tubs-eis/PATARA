# Copyright (c) 2022 Chair for Chip Design for Embedded Computing,
#                    Technische Universitaet Braunschweig, Germany
#                    www.tu-braunschweig.de/en/eis
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
from typing import List

import xmltodict

import Constants
from util.Instruction import Instruction
from util.Processor import Processor


class ConditionalExecutionCode:

    class __ConditionalExecutionCode:
        def __init__(self):
            self.conditionalData = {}
            self.initialize()

        def _createInstructionList(self, instructionList):
            result = []
            for instr in instructionList:
                result.append(Instruction(instr))
            return result


        def initialize(self):
            self.immediateAssembly = None
            file = open(Constants.PATH_INSTRUCTION)
            xml_content = xmltodict.parse(file.read())

            for group in xml_content[Constants.INST_LIST]:
                if group == Constants.CONDITIONAL_READ:
                    conditionVariants = xml_content[Constants.INST_LIST][Constants.CONDITIONAL_READ]
                    for condition in conditionVariants:
                        self.conditionalData[condition] = {}
                        for conditionFlag in conditionVariants[condition]:
                            self.conditionalData[condition][conditionFlag] ={}
                            simd = Constants.vMutable
                            if conditionVariants[condition][conditionFlag]:
                                if Constants.INSTR in conditionVariants[condition][conditionFlag]:
                                    self.conditionalData[condition][conditionFlag][simd] = self._createInstructionList(conditionVariants[condition][conditionFlag][
                                                                                                                           Constants.INSTR])
                                    n=3
                                elif  Constants.REVERSE in  conditionVariants[condition][conditionFlag]:
                                    self.conditionalData[condition][conditionFlag][simd] = self._createInstructionList(
                                        conditionVariants[condition][conditionFlag][
                                            Constants.REVERSE])
                                    n=3
                                else:
                                    for simdVariant in conditionVariants[condition][conditionFlag]:
                                        simdAssembly = Processor().getProcessorFeatureAssembly(Constants.SIMD, simdVariant)
                                        self.conditionalData[condition][conditionFlag][
                                            simdAssembly] = self._createInstructionList(
                                            conditionVariants[condition][conditionFlag][simdVariant][
                                                Constants.REVERSE])
                                    # simd =
                                    # self.conditionalData[condition][conditionFlag] = ]
                                    n=3

                    n=3

    instance = None

    def __init__(self):
        if not ConditionalExecutionCode.instance:
            ConditionalExecutionCode.instance = ConditionalExecutionCode.__ConditionalExecutionCode()
        n=3


    def getPreInstruction(self, simdAssembly, conditionFlag) -> List[Instruction]:
        conditionCode = self.instance.conditionalData[conditionFlag][Constants.CONDITION_PRE_INSTRUCTION]
        if conditionCode:
            if simdAssembly in conditionCode:
                return conditionCode[simdAssembly]
            else:
                return conditionCode[Constants.vMutable]
        else:
            return None

    def getPostInstruction(self, simdAssembly, conditionFlag) -> str:
        conditionCode = self.instance.conditionalData[conditionFlag][Constants.CONDITION_POST_INSTRUCTION]
        if conditionCode:
            if simdAssembly in conditionCode:
                return conditionCode[simdAssembly]
            else:
                return conditionCode[Constants.vMutable]
        else:
            return None

    def getPreReverse(self, simdAssembly, conditionFlag) -> str:
        conditionCode = self.instance.conditionalData[conditionFlag][Constants.CONDITION_PRE_REVERSE]
        if conditionCode:
            if simdAssembly in conditionCode:
                return conditionCode[simdAssembly]
            else:
                return conditionCode[Constants.vMutable]
        else:
            return None


    def getPostReverse(self, simdAssembly, conditionFlag) -> str:
        conditionCode = self.instance.conditionalData[conditionFlag][Constants.CONDITION_POST_REVERSE]
        if conditionCode:
            if simdAssembly in conditionCode:
                return conditionCode[simdAssembly]
            else:
                return conditionCode[Constants.vMutable]
        else:
            return None


    def isEnabled(self, enabledFlags):
        if Constants.CONDITIONAL in enabledFlags:
            enabledCondition = None != enabledFlags[Constants.CONDITIONAL]
            if enabledCondition:
                return Constants.CONDITIONAL_READ == Processor().getAssemlby2Feature(enabledFlags[Constants.CONDITIONAL])
            else:
                return False
        else:
            return False

