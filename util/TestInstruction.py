from typing import List, Dict

from util.ConditionalExecutionCode import ConditionalExecutionCode

from Constants import *
from util.Instruction import Instruction
from util.Processor import Processor


class TestInstruction:

    def __init__(self, originalInstructions: List[str], reverseInstructions: Dict[str, List[str]], instruction: str,
                 specialization, validInstructionList, immediateReverseAssembly: List[Instruction]):
        self.instruction = instruction
        self.validInstructionList = validInstructionList
        self.immediateReverseAssembly = immediateReverseAssembly
        originalInstr = []
        self.interleavingTargetRegister = None
        self.globalMandatoryFeatures = {}
        self.globalMandatoryFeatures[ISSUE_SLOT] = Processor().getRandomIssueSlot()
        for originalInstruction in originalInstructions:
            originalInstr.append(Instruction(originalInstruction))
        self._originalInstructions = originalInstr  # List of OriginalInstruction classes
        self._importReverseInstructions(reverseInstructions)
        self._importSpecialization(specialization)
        self.instructionCount = 0

    def _importSpecialization(self, specialization):
        self.specialization = {}
        if specialization is not None:
            for category in specialization:
                self.specialization[category] = {}
                for featureName in specialization[category]:
                    # try:
                    originalInstruction = [specialization[category][featureName][INSTR]] if isinstance(
                        specialization[category][featureName][INSTR], str) else specialization[category][featureName][
                        INSTR]
                    # except:
                    #     n=3
                    reversiInstruction = {}
                    if isinstance(specialization[category][featureName][REVERSE], dict):
                        # if category == CONDITIONAL_READ:
                        for simd in specialization[category][featureName][REVERSE]:
                            assemlbySIMD = Processor().getProcessorFeatureAssembly(SIMD, simd)

                            reversiInstruction[assemlbySIMD] = [
                                specialization[category][featureName][REVERSE][simd][REVERSE]] if isinstance(
                                specialization[category][featureName][REVERSE][simd][REVERSE], str) else \
                                specialization[category][featureName][REVERSE][simd][REVERSE]
                            n = 3

                    else:
                        reversiInstruction[vMutable] = [specialization[category][featureName][REVERSE]] if isinstance(
                            specialization[category][featureName][REVERSE], str) else \
                        specialization[category][featureName][REVERSE]

                    feature = Processor().getProcessorFeatureAssembly(category, featureName)
                    self.specialization[category][feature] = TestInstruction(originalInstruction, reversiInstruction,
                                                                             self.instruction, {},
                                                                             self.validInstructionList,
                                                                             self.immediateReverseAssembly)

        n = 3

    def copyEnabledFeatures(self, features):
        instructionFEatures = Processor().getAvailableInstructionFeatures(self.instruction)
        self._enabledFeatures = features
        for feature in self._enabledFeatures:
            self.setFeatures(feature, self._enabledFeatures[feature])

    def getInstruction(self) -> str:
        return self.instruction

    def getAssemblyInstructions(self) -> List[Instruction]:
        return self._originalInstructions

    def getReversiAssemblyInstructions(self) -> List[Instruction]:
        return self._reverseInstructions

    def _importReverseInstructions(self, reverseInstructions: Dict[str, List[str]]):  # Dict[str, List[str]]):
        self.reverseMutable = True
        # self.reverseMutable = False
        # if vMutable in reverseInstructions:
        #     self.reverseMutable = True

        self._reverseInstructions = {}
        for simd in reverseInstructions:
            self._reverseInstructions[simd] = []
            for reverseInstruction in reverseInstructions[simd]:
                self._reverseInstructions[simd].append(Instruction(reverseInstruction, self.reverseMutable))

    def getTargetOperand(self) -> str:
        return self.operandAttributes[OPERANDS.TARGET_REGISTER.value]

    def getFocusOperand(self) -> str:
        return self.operandAttributes[OPERANDS.FOCUS_REGISTER.value]

    def getOperands(self):
        return self.operandAttributes

    def getTransferableEnabledFeatures(self):
        transfereableEnabled = {}
        for feature in self._enabledFeatures:
            if (feature != CONDITIONAL and feature != CONDITIONAL_READ):
                transfereableEnabled[feature] = self._enabledFeatures[feature]

        return transfereableEnabled

    def getTransferableReversiEnabledFeatures(self):
        """

        :return: Do not transfer immediate features to reversi code
        """

        transfereableEnabled = self.getTransferableEnabledFeatures()
        transfereableEnabled[IMMEDIATE] = None
        return transfereableEnabled

    def generateCode(self) -> str:
        if self._enabledFeaturesUseSpecialization():
            specializedTestInstruction: TestInstruction = self._getSpecializationTestInstruction()
            specializedTestInstruction.copyEnabledFeatures(self._enabledFeatures)
            specializedTestInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)
            specializedTestInstruction._setOperationRegister(self.operandAttributes)
            specializedTestInstruction.setTargetRegister(self.interleavingTargetRegister)
            return specializedTestInstruction.generateCode()

        code = ""
        code += self.addImmediateCode()
        code += self.addInstructionPreConditionCode()
        for originalInstruction in self._originalInstructions:
            self.instructionCount += 1
            originalInstruction.setFeatures(self.getTransferableReversiEnabledFeatures())
            self.replaceRandValueWithImmediate(originalInstruction)

            if self.isMainInstruction(originalInstruction):
                # originalInstruction.setFeatures(self.getTransferableEnabledFeatures())
                if self._isReadConditionEnabled():
                    originalInstruction.setEnabledFeatures(CONDITIONAL, "CRS")

            originalInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)

            code += originalInstruction.string()
            code += "\n"

        code += self.addInstructionPostConditionCode()
        return code

    def isMainInstruction(self, instruction):
        return instruction.getName().lower() == self.instruction

    def replaceRandValueWithImmediate(self, instruction):
        if self.isMainInstruction(instruction):
            if self._enabledFeatures[IMMEDIATE] == IMMEDIATE_LONG or self._enabledFeatures[
                IMMEDIATE] == IMMEDIATE_SHORT:
                instruction.setFeatures(self.getTransferableEnabledFeatures())
                instruction.enableRandValueRandomImmediate()

    def generateReversiCode(self) -> str:
        if self._enabledFeaturesUseSpecialization():
            specializedTestInstruction: TestInstruction = self._getSpecializationTestInstruction()
            specializedTestInstruction.copyEnabledFeatures(self._enabledFeatures)
            specializedTestInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)
            specializedTestInstruction._setReverseRegister(vMutable, self.operandAttributes)
            specializedTestInstruction.setTargetRegister(self.interleavingTargetRegister)
            return specializedTestInstruction.generateReversiCode()
        code = ""
        # simdMode = vMutable
        # if not self.reverseMutable:
        #     simdMode = self._getSIMDMode()
        simdMode = self._getReversiSIMDMode()

        self._setReverseRegister(simdMode, self.operandAttributes)
        code += self.addReversePreConditionCode()
        code += self.addImmediateCode()
        for reverseInstruction in self._reverseInstructions[simdMode]:
            self.instructionCount += 1
            code += reverseInstruction.getAssembly(enabledFeatures=self.getTransferableReversiEnabledFeatures(),
                                                   globalMandatoryFeatures=self.globalMandatoryFeatures)
            code += "\n"
        code += self.addReversePostConditionCode()
        return code

    def _getSpecializationTestInstruction(self):
        instructionFeatures = Processor().getAvailableInstructionFeatures(self.instruction)
        for feature in self._enabledFeatures:
            if feature in self.specialization:
                if self._isEnabledFeature(feature):
                    assemblerFeatureName = self._enabledFeatures[feature]  # Processor().getFeature(feature, )
                    specializedTestInstruction = self.specialization[feature][assemblerFeatureName]
                    return specializedTestInstruction

    def addImmediateCode(self):
        code = ""
        if self._enabledFeatures[IMMEDIATE]:
            for simd in self.immediateReverseAssembly[self._enabledFeatures[IMMEDIATE]]:
                if simd == vMutable:
                    for instr in self.immediateReverseAssembly[self._enabledFeatures[IMMEDIATE]][vMutable]:
                        instr.setEnabledFeatures(SIMD, self._enabledFeatures[SIMD])
                        instr.setEnabledFeatures(SIGNAGE, self._enabledFeatures[SIGNAGE])
                        instr.setEnabledFeatures(IMMEDIATE, self._enabledFeatures[IMMEDIATE])
                        instr.setOperands(self.operandAttributes)
                        code += instr.string() + "\n"
                else:
                    if self._enabledFeatures[SIMD] in simd:
                        for instr in self.immediateReverseAssembly[self._enabledFeatures[IMMEDIATE]][simd]:
                            instr.setEnabledFeatures(SIMD, self._enabledFeatures[SIMD])
                            instr.setEnabledFeatures(SIGNAGE, self._enabledFeatures[SIGNAGE])
                            instr.setEnabledFeatures(IMMEDIATE, self._enabledFeatures[IMMEDIATE])
                            instr.setOperands(self.operandAttributes)
                            code += instr.string() + "\n"

        return code

    def reset_features(self):
        for instr in self._originalInstructions:
            instr.resetFeatures()
        if self.reverseMutable:
            for instr in self._reverseInstructions[vMutable]:
                instr.resetFeatures()
        else:
            raise Exception("How to handle SIMD enabling features?")

    def setFeatures(self, key, value):
        for instr in self._originalInstructions:
            instr.setEnabledFeatures(key, value)
        if self.reverseMutable:
            for simdVariants in self._reverseInstructions:
                for instr in self._reverseInstructions[simdVariants]:
                    if instr.features is None:
                        continue
                    instr.setEnabledFeatures(key, value)

    def getEnabledFeature(self, feature):
        return self._enabledFeatures[feature]

    def set_random_features(self, immediateProbability=0):  # probability = prob of immediate
        features = Processor().getAvailableInstructionFeatures(self.instruction)
        # features = self._originalInstructions[0].get_features() # dict of features
        feature_stats = Processor().random_enabled_features(self.instruction, immediateProbability)

        self._enabledFeatures = feature_stats

    def setEnableFeature(self, feature, featureAssembly):
        """
        Set a Feature to a Value. Value is based on writing in Processor description.
        Be careful this function should only be used for debugging
        :param feature:
        :param featureAssembly:
        :return:
        """
        features = Processor().get_instr_features(self.instruction)
        self._enabledFeatures[feature] = featureAssembly

    def setEnableFeatureIndex(self, feature, index):
        """Set a Feature to a Index (integer position of feature in Available Features of the instruction).
                Be careful this function should only be used for debugging"""
        features = Processor().getAvailableInstructionFeatures(self.instruction)
        featureAssembly = features[feature][index]
        self._enabledFeatures[feature] = featureAssembly

    def getAssemblerFeatures(self):
        features = Processor().getAvailableInstructionFeatures(self.instruction)
        result = {}
        for key in self._enabledFeatures:
            result[key] = features[key][self._enabledFeatures[key]]
        return result

    def generateRandomOperands(self, FocusRegister=None):
        """
        Get Random operands.
        :param FocusRegister: Provide a Focusregister, if it is empty, a random focusregister will be selected.
        :return:
        """
        generateFocusRegister = True
        if FocusRegister is not None:
            generateFocusRegister = False

        self.operandAttributes = Processor().generateRandomOperands(self._enabledFeatures, generateFocusRegister,
                                                                    FocusRegister)

        if FocusRegister is not None:
            # self.focusReg = FocusRegister
            self.operandAttributes[FOCUS_REGISTER] = FocusRegister

        self._setOperationRegister(self.operandAttributes)

        self._setOperandsReversi()

    def _setOperandsReversi(self):
        simdMode = vMutable
        if not self.reverseMutable:
            simdMode = self._getReversiSIMDMode()
        self._setReverseRegister(simdMode, self.operandAttributes)

    def setTargetRegister(self, targetRegister):
        self.interleavingTargetRegister = targetRegister
        self._setOperandsReversi()

    def _enabledFeaturesUseSpecialization(self):
        if len(self.specialization.items()) == 0:
            return False

        if CONDITIONAL_READ in self.specialization:
            if Processor().getProcessorFeatureAssembly(CONDITIONAL, CONDITIONAL_READ) == self._enabledFeatures[
                CONDITIONAL]:
                return self._enabledFeatures[CONDITIONAL_READ] in self.specialization[CONDITIONAL_READ]

        instructionFeatures = Processor().getAvailableInstructionFeatures(self.instruction)
        for feature in self._enabledFeatures:
            if self._isEnabledFeature(feature):
                if feature in self.specialization:
                    assemblerFeatureName = self._enabledFeatures[feature]  # Processor().getFeature(feature, )
                    if assemblerFeatureName in instructionFeatures[feature]:
                        return assemblerFeatureName in self.specialization[feature]
                # return instructionFeatures[feature] in self.specialization[feature]
        return False

    def _isEnabledFeature(self, feature):
        if feature is CONDITIONAL_READ:
            return self._enabledFeatures[CONDITIONAL]
        return self._enabledFeatures[feature]

    def _useMemorySpecialization(self):
        usedSpecialization = self._enabledFeaturesUseSpecialization()
        return usedSpecialization

    def _getReversiSIMDMode(self):
        if vMutable in self._reverseInstructions:
            return vMutable
        else:
            return self._enabledFeatures[SIMD]

    def _setOperationRegister(self, operandAttributes):
        self.operandAttributes = operandAttributes
        for instr in self._originalInstructions:
            instr.resetFeatures()
            if instr.getName().lower() in self.validInstructionList:
                instr.setFeatures(self._enabledFeatures)
            instr.setOperands(self.operandAttributes)

    def _setReverseRegister(self, simdMode, operandAttributes):
        self.operandAttributes = operandAttributes
        try:
            for rev_instr in self._reverseInstructions[simdMode]:
                rev_instr.resetFeatures()
                if rev_instr.getName().lower() in self.validInstructionList:
                    rev_instr.setFeatures(self._enabledFeatures)
                rev_instr.setOperands(self.operandAttributes)
                rev_instr.setOverrideTargetOperand(self.interleavingTargetRegister)
        except:
            n = 3

    def __str__(self) -> str:
        description = ""
        for original in self._originalInstructions:
            description += original.string()
            description += "\n"
        description += " ->\n"
        for reverse in self._reverseInstructions:
            description += reverse.string()
            description += "\n"
        return description

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self._originalInstructions == other._originalInstructions and self._reverseInstructions == other._reverseInstructions

    def setGlobalMandatoryFeatures(self, globalMandatoryFeatures):
        self.globalMandatoryFeatures = globalMandatoryFeatures

    def getInstructionCount(self):
        if self._enabledFeaturesUseSpecialization():
            specializedTestInstruction: TestInstruction = self._getSpecializationTestInstruction()
            self.instructionCount = specializedTestInstruction.getInstructionCount()
        return self.instructionCount

    def _isReadConditionEnabled(self):
        if CONDITIONAL in self._enabledFeatures:
            foundCondition = None != self._enabledFeatures[CONDITIONAL]
            if foundCondition:
                return Processor().getAssemlby2Feature(self._enabledFeatures[CONDITIONAL]) == CONDITIONAL_READ
            else:
                return False
        else:
            return False

    def _generateInstructionListAssembly(self, instructionList, globalMandatoryFeatures={},
                                         hasOverridingTargetRegister=False):
        code = ""
        if instructionList:
            for instruction in instructionList:
                self.instructionCount += 1
                instruction.setOperands(self.operandAttributes)
                if hasOverridingTargetRegister:
                    instruction.setOverrideTargetOperand(self.interleavingTargetRegister)
                code += instruction.getAssembly(enabledFeatures=self.getTransferableReversiEnabledFeatures(),
                                                globalMandatoryFeatures=globalMandatoryFeatures)
                code += "\n"
        return code

    def addInstructionPreConditionCode(self) -> str:
        conditionalExec = ConditionalExecutionCode()
        if conditionalExec.isEnabled(self._enabledFeatures):
            conditionFlag = self._enabledFeatures[CONDITIONAL_READ]
            instructionList = conditionalExec.getPreInstruction(self._enabledFeatures[SIMD],
                                                                conditionFlag=conditionFlag)
            return self._generateInstructionListAssembly(instructionList) + "\n"

        return ""

    def addInstructionPostConditionCode(self) -> str:
        conditionalExec = ConditionalExecutionCode()
        if conditionalExec.isEnabled(self._enabledFeatures):
            conditionFlag = self._enabledFeatures[CONDITIONAL_READ]
            instructionList = conditionalExec.getPostInstruction(self._enabledFeatures[SIMD],
                                                                 conditionFlag=conditionFlag)
            return self._generateInstructionListAssembly(instructionList) + "\n"

        return ""

    def addReversePreConditionCode(self) -> str:
        conditionalExec = ConditionalExecutionCode()
        if conditionalExec.isEnabled(self._enabledFeatures):
            conditionFlag = self._enabledFeatures[CONDITIONAL_READ]
            instructionList = conditionalExec.getPreReverse(self._enabledFeatures[SIMD], conditionFlag=conditionFlag)
            return self._generateInstructionListAssembly(instructionList, hasOverridingTargetRegister=True) + "\n"

        return ""

    def addReversePostConditionCode(self) -> str:
        conditionalExec = ConditionalExecutionCode()
        if conditionalExec.isEnabled(self._enabledFeatures):
            conditionFlag = self._enabledFeatures[CONDITIONAL_READ]
            instructionList = conditionalExec.getPostReverse(self._enabledFeatures[SIMD],
                                                             conditionFlag=conditionFlag)
            return self._generateInstructionListAssembly(instructionList, hasOverridingTargetRegister=True) + "\n"

        return ""
