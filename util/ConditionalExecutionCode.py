# Copyright (c) 2023 Chair for Chip Design for Embedded Computing,
#                    Technische Universitaet Braunschweig, Germany
#                    www.tu-braunschweig.de/en/eis
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


from typing import List

import xmltodict

from Constants import *
from util.Instruction import Instruction


class ConditionalExecutionCode:
    class __ConditionalExecutionCode:
        def __init__(self, architecture):
            self.conditionalData = {}
            self.initialize(architecture)

        def _createInstructionList(self, instructionList):
            result = []
            for instr in instructionList:
                result.append(Instruction(instr))
            return result

        def initialize(self, architecture):
            self.immediateAssembly = None
            file = open(get_path_instruction(architecture))
            xml_content = xmltodict.parse(file.read())

            for group in xml_content[INST_LIST]:
                if group == CONDITIONAL_READ:
                    conditionVariants = xml_content[INST_LIST][CONDITIONAL_READ]
                    for condition in conditionVariants:
                        self.conditionalData[condition] = {}
                        for conditionFlag in conditionVariants[condition]:
                            self.conditionalData[condition][conditionFlag] = {}
                            simd = V_MUTABLE
                            if conditionVariants[condition][conditionFlag]:
                                if INSTR in conditionVariants[condition][conditionFlag]:
                                    self.conditionalData[condition][conditionFlag][simd] = self._createInstructionList(
                                        conditionVariants[condition][conditionFlag][
                                            INSTR])
                                elif REVERSE in conditionVariants[condition][conditionFlag]:
                                    self.conditionalData[condition][conditionFlag][simd] = self._createInstructionList(
                                        conditionVariants[condition][conditionFlag][
                                            REVERSE])
                                else:
                                    for simdVariant in conditionVariants[condition][conditionFlag]:
                                        # simdAssembly = Processor().getProcessorFeatureAssembly(SIMD, simdVariant)
                                        self.conditionalData[condition][conditionFlag][
                                            simdVariant] = self._createInstructionList(
                                            conditionVariants[condition][conditionFlag][simdVariant][
                                                REVERSE])
            n = 3

    instance = None

    def __init__(self, architecture="rv32imc"):
        if not ConditionalExecutionCode.instance:
            ConditionalExecutionCode.instance = ConditionalExecutionCode.__ConditionalExecutionCode(architecture)
        n = 3

    def getPreInstruction(self, simdAssembly, conditionFlag) -> List[Instruction]:
        conditionCode = self.instance.conditionalData[conditionFlag][CONDITION_PRE_INSTRUCTION]
        if conditionCode:
            if simdAssembly in conditionCode:
                return conditionCode[simdAssembly]
            else:
                return conditionCode[V_MUTABLE]
        else:
            return None

    def getPostInstruction(self, simdAssembly, conditionFlag) -> str:
        conditionCode = self.instance.conditionalData[conditionFlag][CONDITION_POST_INSTRUCTION]
        if conditionCode:
            if simdAssembly in conditionCode:
                return conditionCode[simdAssembly]
            else:
                return conditionCode[V_MUTABLE]
        else:
            return None

    def getPreReverse(self, simdAssembly, conditionFlag) -> str:
        conditionCode = self.instance.conditionalData[conditionFlag][CONDITION_PRE_REVERSE]
        if conditionCode:
            if simdAssembly in conditionCode:
                return conditionCode[simdAssembly]
            else:
                return conditionCode[V_MUTABLE]
        else:
            return None

    def getPostReverse(self, simdAssembly, conditionFlag) -> str:
        conditionCode = self.instance.conditionalData[conditionFlag][CONDITION_POST_REVERSE]
        if conditionCode:
            if simdAssembly in conditionCode:
                return conditionCode[simdAssembly]
            else:
                return conditionCode[V_MUTABLE]
        else:
            return None

    def isEnabled(self, enabledFlags):
        if CONDITIONAL in enabledFlags:
            return CONDITIONAL_READ == enabledFlags[CONDITIONAL]
        else:
            return False
