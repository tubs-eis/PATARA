# Copyright (c) 2023 Chair for Chip Design for Embedded Computing,
#                    Technische Universitaet Braunschweig, Germany
#                    www.tu-braunschweig.de/en/eis
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


from typing import List, Dict

from Constants import *
from util.ConditionalExecutionCode import ConditionalExecutionCode
from util.Instruction import Instruction
from util.Processor import Processor


class TestInstruction:

    def __init__(self, originalInstructions: List[str], preplainInstr: List[str], plainInstructions: List[str],
                 postPlainInstructions: List[str], reverseInstructions: Dict[str, List[str]], instruction: str,
                 specialization, validInstructionList, immediateReverseAssembly: List[Instruction], type: str,
                 specialImmediates: List[int], icacheMissCandidate=False, iCacheRepetition=[]):
        self.instruction = instruction
        self.validInstructionList = validInstructionList
        self.operandAttributes = {}
        self.immediateReverseAssembly = immediateReverseAssembly  # just immediate assembly from DataBank
        originalInstr = []
        self.interleavingTargetRegister = None
        self.globalMandatoryFeatures = {}
        self.globalMandatoryFeatures[ISSUE_SLOT] = Processor().getRandomIssueSlot()
        for originalInstruction in originalInstructions:
            originalInstr.append(Instruction(originalInstruction))
        self._modInstructions: List[Instruction] = originalInstr  # List of OriginalInstruction classes
        plainInstr = []
        for plainInstruction in plainInstructions:
            plainInstr.append(Instruction(plainInstruction))
        self._sequenceInstructions: List[Instruction] = plainInstr
        self._preSequenceInstructions: List[Instruction] = []
        for instr in preplainInstr:
            self._preSequenceInstructions.append(Instruction(instr))
        self._postPlainInstructions: List[Instruction] = []
        for instr in postPlainInstructions:
            self._postPlainInstructions.append(Instruction(instr))
        self._importReverseInstructions(reverseInstructions)
        self._importSpecialization(specialization)
        self._checkNewPlainTargetReg()
        self._checkBranchTargets()
        self.specialImmediates = specialImmediates
        self.instructionCount = 0
        self.generateCode = True
        self.icacheMissCandidate = icacheMissCandidate
        self.iCacheJump = False
        self.iCacheRepetition = []
        for instr in iCacheRepetition:
            self.iCacheRepetition.append(Instruction(instr))
        self._enabledFeatures = {}
        self.type = type

    def _checkNewPlainTargetReg(self):
        self.newSequenceTargetReg = False
        for instr in self._sequenceInstructions:
            if OPERANDS.Sequence_NEW_TARGET_REGISTER.value in instr._assembly:
                self.newSequenceTargetReg = True

    def isImemCacheMissCandidate(self):
        return self.icacheMissCandidate

    def setICacheJump(self):
        self.iCacheJump = True

    def isICacheJump(self):
        return self.iCacheJump

    def _checkBranchTargets(self):
        self.hasBranchTargetAcrossTestcase = False
        modBranch = False
        revTarget = False
        for instr in self._modInstructions:
            if OPERANDS.BRANCH_INDEX.value in instr.getRawAssembly():
                modBranch = True
        for instr in self._reverseInstructions[self._getDefaultReversiSIMDMode()]:
            if OPERANDS.BRANCH_INDEX.value + Processor().getBranchTargetLabel() in instr.getRawAssembly():
                revTarget = True

        self.hasBranchTargetAcrossTestcase = modBranch and revTarget

    def hasBranchAcrossTestCase(self):
        return self.hasBranchTargetAcrossTestcase

    def _importSpecialization(self, specialization):
        self.specialization = {}
        if specialization is not None:
            for category in specialization:
                self.specialization[category] = {}
                for featureName in specialization[category]:
                    originalInstruction = [specialization[category][featureName][INSTR]] if isinstance(
                        specialization[category][featureName][INSTR], str) else specialization[category][featureName][
                        INSTR]
                    plainInstruction = ([specialization[category][featureName][SEQUENCE_INSTR]] if isinstance(
                        specialization[category][featureName][SEQUENCE_INSTR], str) else
                                        specialization[category][featureName][SEQUENCE_INSTR]) if SEQUENCE_INSTR in \
                                                                                                  specialization[
                                                                                                      category][
                                                                                                      featureName] else []
                    prePlainInstruction = ([specialization[category][featureName][PRE_SEQUENCE_INSTR]] if isinstance(
                        specialization[category][featureName][PRE_SEQUENCE_INSTR], str) else
                                           specialization[category][featureName][
                                               PRE_SEQUENCE_INSTR]) if PRE_SEQUENCE_INSTR in specialization[category][
                        featureName] else []
                    postPlainInstructions = ([specialization[category][featureName][POST_SEQUENCE_INSTR]] if isinstance(
                        specialization[category][featureName][POST_SEQUENCE_INSTR], str) else
                                             specialization[category][featureName][
                                                 POST_SEQUENCE_INSTR]) if POST_SEQUENCE_INSTR in \
                                                                          specialization[category][featureName] else []

                    reversiInstruction = {}
                    if isinstance(specialization[category][featureName][REVERSE], dict):
                        for simd in specialization[category][featureName][REVERSE]:
                            if simd == MANDATORY_FEATURE:  # if only one reverse instruction with enabled feature, it is dict but not simd
                                reversiInstruction[V_MUTABLE] = [specialization[category][featureName][REVERSE]]
                                break
                            else:
                                reversiInstruction[simd] = [
                                    specialization[category][featureName][REVERSE][simd][REVERSE]] if isinstance(
                                    specialization[category][featureName][REVERSE][simd][REVERSE], str) else \
                                    specialization[category][featureName][REVERSE][simd][REVERSE]


                    else:
                        reversiInstruction[V_MUTABLE] = [specialization[category][featureName][REVERSE]] if isinstance(
                            specialization[category][featureName][REVERSE], str) else \
                            specialization[category][featureName][REVERSE]

                    subSpecialization = {}
                    if SPECIALIZATION in specialization[category][featureName]:
                        subSpecialization = specialization[category][featureName][SPECIALIZATION]

                    intImms = self._generateSpecialImmediates(specialization[category][featureName])

                    self.specialization[category][featureName] = TestInstruction(originalInstruction,
                                                                                 prePlainInstruction, plainInstruction,
                                                                                 postPlainInstructions,
                                                                                 reversiInstruction, self.instruction,
                                                                                 subSpecialization,
                                                                                 self.validInstructionList,
                                                                                 self.immediateReverseAssembly, type="",
                                                                                 specialImmediates=intImms)

    def _generateSpecialImmediates(self, temp):
        intImms = []
        if SPECIAL_IMMEDIATES in temp:
            immediates = temp[SPECIAL_IMMEDIATES]
            immList = immediates.split(INTEGER_DELIMITER)
            intImms = []
            for i in immList:
                intImms.append(int(i))
        return intImms

    def getSpecialImmediates(self):
        return self.specialImmediates

    def hasSpecialImmediates(self):
        return len(self.specialImmediates) > 0

    def generateSpecialImmediateCode(self):
        self.replaceOperands()

    def copyEnabledFeatures(self, features):
        self._enabledFeatures = features
        for feature in self._enabledFeatures:
            self.setFeatures(feature, self._enabledFeatures[feature])

    def getInstruction(self) -> str:
        return self.instruction

    def _importReverseInstructions(self, reverseInstructions: Dict[str, List[str]]):  # Dict[str, List[str]]):
        self.reverseMutable = True

        self._reverseInstructions: [Dict[str, List[Instruction]]] = {}
        for simd in reverseInstructions:
            self._reverseInstructions[simd] = []
            for reverseInstruction in reverseInstructions[simd]:
                self._reverseInstructions[simd].append(Instruction(reverseInstruction, self.reverseMutable))

    def getTargetOperand(self) -> str:
        return self.operandAttributes[OPERANDS.TARGET_REGISTER.value]

    def getSequenceTargetOperand(self) -> str:
        return self.operandAttributes[OPERANDS.Sequence_TARGET_REGISTER.value]

    def getNewSequenceTargetOperand(self) -> str:
        return self.operandAttributes[OPERANDS.Sequence_NEW_TARGET_REGISTER.value]

    def getFocusOperand(self) -> str:
        return self.operandAttributes[OPERANDS.FOCUS_REGISTER.value]

    def getPlainFocusOperand(self) -> str:
        return self.operandAttributes[OPERANDS.PLAIN_FOCUS_REGISTER.value]

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

    def generateModificationCode(self, sequenceDebugInfo=-1) -> str:
        if self._enabledFeaturesUseSpecialization():
            specializedTestInstruction: TestInstruction = self._getSpecializationTestInstruction()
            specializedTestInstruction.copyEnabledFeatures(self._enabledFeatures)
            if self.generateCode:
                specializedTestInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)
                specializedTestInstruction._setOperationRegister(self.operandAttributes)
                specializedTestInstruction.setTargetRegister(self.interleavingTargetRegister)
            if not self.generateCode:
                specializedTestInstruction.generateCode = False
            code = specializedTestInstruction.generateModificationCode()
            if not self.generateCode:
                specializedTestInstruction.generateCode = True
            return code

        if self.iCacheJump:
            # generate Sequence code
            code = ""
            code += Processor().get_assembler_comment() + "TESTING ICACHE JUMP SEQEUNCE \n"
            code += self.generatePreSequenceCode()
            code += self.generateSequenceRepetitionCode()
            code += "\n"

            return code

        else:
            code = ""
            code += self.addImmediateCode()
            code += self.addInstructionPreConditionCode()
            code += Processor().get_assembler_comment() + self.getInstruction()
            if sequenceDebugInfo > -1:
                code += " " + str(sequenceDebugInfo)
            code += "\n"

            for originalInstruction in self._modInstructions:
                self.instructionCount += 1
                originalInstruction.setFeatures(self.getTransferableReversiEnabledFeatures())
                self.replaceRandValueWithImmediate(originalInstruction)

                if self.isMainInstruction(originalInstruction):
                    if self._isReadConditionEnabled():
                        originalInstruction.setEnabledFeatures(CONDITIONAL, CONDITIONAL_SET_READ)

                originalInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)

                code += originalInstruction.string()
                code += "\n"

            code += self.addInstructionPostConditionCode()
            return code

    def generatePreSequenceCode(self) -> str:
        if self._enabledFeaturesUseSpecialization():
            specializedTestInstruction: TestInstruction = self._getSpecializationTestInstruction()
            specializedTestInstruction.copyEnabledFeatures(self._enabledFeatures)
            if self.generateCode:
                specializedTestInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)
                specializedTestInstruction._setOperationRegister(self.operandAttributes)
                specializedTestInstruction.setTargetRegister(self.interleavingTargetRegister)
            if not self.generateCode:
                specializedTestInstruction.generateCode = False
            code = specializedTestInstruction.generatePreSequenceCode()
            if not self.generateCode:
                specializedTestInstruction.generateCode = True
            return code

        code = ""
        for plainInstruction in self._preSequenceInstructions:
            self.instructionCount += 1
            plainInstruction.setFeatures(self.getTransferableReversiEnabledFeatures())
            if self.generateCode:
                self.replaceRandValueWithImmediate(plainInstruction)
                plainInstruction.setOperands(self.operandAttributes)
                plainInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)

                prePlainCode = plainInstruction.string()
                if prePlainCode:
                    code += prePlainCode
                    code += "\n"
        return code

    def generateSequenceCode(self) -> str:
        if self._enabledFeaturesUseSpecialization():
            specializedTestInstruction: TestInstruction = self._getSpecializationTestInstruction()
            specializedTestInstruction.copyEnabledFeatures(self._enabledFeatures)
            if self.generateCode:
                specializedTestInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)
                specializedTestInstruction._setOperationRegister(self.operandAttributes)
                specializedTestInstruction.setTargetRegister(self.interleavingTargetRegister)
            if not self.generateCode:
                specializedTestInstruction.generateCode = False
            code = specializedTestInstruction.generateSequenceCode()
            if not self.generateCode:
                specializedTestInstruction.generateCode = True
            return code

        code = ""
        for plainInstruction in self._sequenceInstructions:
            self.instructionCount += 1
            if self.generateCode:
                plainInstruction.setFeatures(self.getTransferableReversiEnabledFeatures())
                self.replaceRandValueWithImmediate(plainInstruction)

                if self.isMainInstruction(plainInstruction):
                    if self._isReadConditionEnabled():
                        plainInstruction.setEnabledFeatures(CONDITIONAL, CONDITIONAL_SET_READ)

                plainInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)

                code += plainInstruction.string()
                code += "\n"
        return code

    def generateSequenceRepetitionCode(self) -> str:
        code = ""
        for index in range(len(self.iCacheRepetition) - 2):
            plainInstruction = self.iCacheRepetition[index]
            self.instructionCount += 1
            if self.generateCode:
                plainInstruction.setFeatures(self.getTransferableReversiEnabledFeatures())
                self.replaceRandValueWithImmediate(plainInstruction)

                plainInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)

                code += plainInstruction.string()
                code += "\n"

        # Repeat Destroy Instruction to evict caches lines
        plainInstruction = self.iCacheRepetition[-2]
        if self.generateCode:
            plainInstruction.setFeatures(self.getTransferableReversiEnabledFeatures())
            self.replaceRandValueWithImmediate(plainInstruction)

            plainInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)

        if Processor().hasIMemJump():
            instrRepgs = Processor().getIMemJumpInstructions() - len(self._sequenceInstructions) - len(
                self.iCacheRepetition)
            code += Processor().get_assembler_comment() + " jump imem Cache line\n"
            for i in range(instrRepgs):
                code += plainInstruction.string()
                code += "\n"
                self.instructionCount += 1

        # set Branch Target
        plainInstruction = self.iCacheRepetition[-1]
        plainInstruction.setFeatures(self.getTransferableReversiEnabledFeatures())
        if self.generateCode:
            self.replaceRandValueWithImmediate(plainInstruction)

            plainInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)
            code += plainInstruction.string()
        self.instructionCount += 1
        return code

    def generatePostSequenceCode(self) -> str:
        if self._enabledFeaturesUseSpecialization():
            specializedTestInstruction: TestInstruction = self._getSpecializationTestInstruction()
            specializedTestInstruction.copyEnabledFeatures(self._enabledFeatures)
            if self.generateCode:
                specializedTestInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)
                specializedTestInstruction._setOperationRegister(self.operandAttributes)
                specializedTestInstruction.setTargetRegister(self.interleavingTargetRegister)
            if not self.generateCode:
                specializedTestInstruction.generateCode = False
            code = specializedTestInstruction.generatePostSequenceCode()
            if not self.generateCode:
                specializedTestInstruction.generateCode = True
            return code

        code = ""
        for plainInstruction in self._postPlainInstructions:
            self.instructionCount += 1
            if self.generateCode:
                plainInstruction.setFeatures(self.getTransferableReversiEnabledFeatures())
                self.replaceRandValueWithImmediate(plainInstruction)
                plainInstruction.setOperands(self.operandAttributes)

                if self.isMainInstruction(plainInstruction):
                    if self._isReadConditionEnabled():
                        plainInstruction.setEnabledFeatures(CONDITIONAL, CONDITIONAL_SET_READ)

                plainInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)

                code += plainInstruction.string()
                code += "\n"
        return code

    def getEnabledFeatures(self):
        return self._enabledFeatures

    def isMainInstruction(self, instruction):
        return instruction.getName().lower() == self.instruction

    def replaceRandValueWithImmediate(self, instruction):
        if self.isMainInstruction(instruction):
            if self._enabledFeatures[IMMEDIATE]:
                instruction.setFeatures(self.getTransferableEnabledFeatures())
                instruction.enableRandValueRandomImmediate()

    def _selectSpecializationCode(self, function):
        '''
        First attemptemt at reusing function across multiple object methods (reverse, modification, sequence, pre and post sequence)
        :param function:
        :return:
        '''
        if self._enabledFeaturesUseSpecialization():
            specializedTestInstruction: TestInstruction = self._getSpecializationTestInstruction()
            specializedTestInstruction.copyEnabledFeatures(self._enabledFeatures)
            if self.generateCode:
                specializedTestInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)
                specializedTestInstruction._setReverseRegister(V_MUTABLE, self.operandAttributes)
                specializedTestInstruction.setTargetRegister(self.interleavingTargetRegister)
            if not self.generateCode:
                specializedTestInstruction.generateCode = False
            code = function()
            # code = specializedTestInstruction.function()
            if not self.generateCode:
                specializedTestInstruction.generateCode = True
            return code

    def generateReversiCode(self, sequenceDebugInfo=-1) -> str:
        if self.iCacheJump:
            return ""
        else:
            if self._enabledFeaturesUseSpecialization():
                specializedTestInstruction: TestInstruction = self._getSpecializationTestInstruction()
                specializedTestInstruction.copyEnabledFeatures(self._enabledFeatures)
                if self.generateCode:
                    specializedTestInstruction.setGlobalMandatoryFeatures(self.globalMandatoryFeatures)
                    specializedTestInstruction._setReverseRegister(V_MUTABLE, self.operandAttributes)
                    specializedTestInstruction.setTargetRegister(self.interleavingTargetRegister)
                if not self.generateCode:
                    specializedTestInstruction.generateCode = False
                code = specializedTestInstruction.generateReversiCode()
                if not self.generateCode:
                    specializedTestInstruction.generateCode = True
                # test moving stuff to functions for nicer code
                # controlCode = self._selectSpecializationCode(self._getSpecializationTestInstruction().generateReversiCode())
                # if code != controlCode:
                #     n=3
                return code
            code = ""
            simdMode = self._getReversiSIMDMode()

            if self.generateCode:
                self._setReverseRegister(simdMode, self.operandAttributes)
            code += self.addReversePreConditionCode()
            code += self.addImmediateCode()
            if sequenceDebugInfo > -1:
                code += Processor().get_assembler_comment() + "REVERSE:" + self.getInstruction() + " " + str(
                    sequenceDebugInfo) + "\n"
            else:
                code += Processor().get_assembler_comment() + "REVERSE:" + self.getInstruction() + "\n"

            for reverseInstruction in self._reverseInstructions[simdMode]:
                self.instructionCount += 1
                if self.generateCode:
                    self.replaceRandValueWithImmediate(reverseInstruction)
                    code += reverseInstruction.getAssembly(enabledFeatures=self.getTransferableReversiEnabledFeatures(),
                                                           globalMandatoryFeatures=self.globalMandatoryFeatures)
                    code += "\n"
            code += self.addReversePostConditionCode()
            return code

    def _getSpecializationTestInstruction(self):
        for feature in self._enabledFeatures:
            if feature in self.specialization:
                if self._isEnabledFeature(feature):
                    assemblerFeatureName = self._enabledFeatures[feature]
                    if assemblerFeatureName in self.specialization[feature]:
                        return self.specialization[feature][assemblerFeatureName]

    def addImmediateCode(self):
        code = ""
        if self._enabledFeatures[IMMEDIATE] and self.immediateReverseAssembly:
            code += "\n" + Processor().get_assembler_comment() + "Immediate Code" + "\n"
            for simd in self.immediateReverseAssembly[self._enabledFeatures[IMMEDIATE]]:
                if simd == V_MUTABLE:
                    for instr in self.immediateReverseAssembly[self._enabledFeatures[IMMEDIATE]][V_MUTABLE]:
                        instr.setEnabledFeatures(SIMD, self._enabledFeatures[SIMD])
                        instr.setEnabledFeatures(SIGNAGE, self._enabledFeatures[SIGNAGE])
                        instr.setEnabledFeatures(IMMEDIATE, self._enabledFeatures[IMMEDIATE])
                        if self.generateCode:
                            instr.setOperands(self.operandAttributes)
                            code += instr.string() + "\n"
                        self.instructionCount += 1
                else:
                    if self._enabledFeatures[SIMD] in simd:
                        for instr in self.immediateReverseAssembly[self._enabledFeatures[IMMEDIATE]][simd]:
                            instr.setEnabledFeatures(SIMD, self._enabledFeatures[SIMD])
                            instr.setEnabledFeatures(SIGNAGE, self._enabledFeatures[SIGNAGE])
                            instr.setEnabledFeatures(IMMEDIATE, self._enabledFeatures[IMMEDIATE])
                            if self.generateCode:
                                instr.setOperands(self.operandAttributes)
                                code += instr.string() + "\n"
                            self.instructionCount += 1
        else:
            code = "\n"

        return code

    def reset_features(self):
        for instr in self._modInstructions:
            instr.resetFeatures()
        for instr in self._sequenceInstructions:
            instr.resetFeatures()
        if self.reverseMutable:
            for instr in self._reverseInstructions[V_MUTABLE]:
                instr.resetFeatures()
        else:
            raise Exception("How to handle SIMD enabling features?")

    def setFeatures(self, key, value):
        for instr in self._modInstructions:
            instr.setEnabledFeatures(key, value)
        for instr in self._sequenceInstructions:
            instr.setEnabledFeatures(key, value)
        if self.reverseMutable:
            for simdVariants in self._reverseInstructions:
                for instr in self._reverseInstructions[simdVariants]:
                    if instr.features is None:
                        continue
                    instr.setEnabledFeatures(key, value)

    def getEnabledFeature(self, feature):
        return self._enabledFeatures[feature]

    def set_random_features(self, immediateProbability=0.0, switchProbability=0.0):  # probability = prob of immediate
        feature_stats = Processor().random_enabled_features(self.instruction, immediateProbability, switchProbability)

        self._enabledFeatures = feature_stats

    def isOutsideSequenceUsed(self, outsideSequenceUsage):
        # if icacheMiss is triggered Outside of a sequence, registers from seqeunces get used
        # outside of seqeunces these registers are not protected, thus change plaintemp to t2
        if outsideSequenceUsage and self.iCacheJump:
            # overwrite pre seqeuence code
            if self._enabledFeaturesUseSpecialization():
                testInstructions = self._getSpecializationTestInstruction()
            else:
                testInstructions = self._preSequenceInstructions
            for instr in testInstructions:
                instr.replaceRegisterTemplate(OPERANDS.Sequence_TEMP.value, "t1")

            # replace icache Repetition instructions
            for instr in self.iCacheRepetition:
                instr.replaceRegisterTemplate(OPERANDS.Sequence_TEMP.value, "t1")
            n = 3

    def setEnableFeature(self, feature, featureAssembly):
        """
        Set a Feature to a Value. Value is based on writing in Processor description.
        Be careful this function should only be used for debugging
        """
        self._enabledFeatures[feature] = featureAssembly

    def setEnableFeatureName(self, feature: str, attribute: str):
        """Enable a Feature to the given attribute. Be careful this function should only be used for debugging.

        Args:
            feature (str): name of the feature to enable
            attribute (str): name of the attribute to set the feature to.
        """
        self._enabledFeatures[feature] = attribute

    def generateRandomOperands(self, focusRegister=None, sequence=False, sequenceFocusRegister=None,
                               blockRandomRegister=False):
        """
        Get Random operands.
        :param FocusRegister: Provide a Focusregister, if it is empty, a random focusregister will be selected.
        :return:
        """
        generateFocusRegister = True if focusRegister is None else False

        if self.isICacheJump():
            sequence = True

        self.operandAttributes = Processor().generateRandomOperands(self._enabledFeatures, generateFocusRegister,
                                                                    focusRegister, sequence, sequenceFocusRegister,
                                                                    self.newSequenceTargetReg, blockRandomRegister)

        self._setOperationRegister(self.operandAttributes)
        # if "b" in self.instruction

        self._setOperandsReversi()

    def _setOperandsReversi(self):
        simdMode = V_MUTABLE
        if not self.reverseMutable:
            simdMode = self._getReversiSIMDMode()
        if simdMode in self._reverseInstructions:
            self._setReverseRegister(simdMode, self.operandAttributes)
        else:
            for simd in self._reverseInstructions:
                self._setReverseRegister(simd, self.operandAttributes)

    def setTargetRegister(self, targetRegister):
        self.interleavingTargetRegister = targetRegister
        self._setOperandsReversi()

    def _enabledFeaturesUseSpecialization(self):
        if len(self.specialization.items()) == 0:
            return False

        if CONDITIONAL_READ in self.specialization and self._enabledFeatures[CONDITIONAL] == CONDITIONAL_READ:
            return self._enabledFeatures[CONDITIONAL_READ] in self.specialization[CONDITIONAL_READ]

        for feature in self._enabledFeatures:
            if self._isEnabledFeature(feature):
                if feature in self.specialization:
                    assemblerFeatureName = self._enabledFeatures[feature]
                    if assemblerFeatureName in self.specialization[feature]:
                        return True
        return False

    def _isEnabledFeature(self, feature):
        if feature is CONDITIONAL_READ:
            return self._enabledFeatures[CONDITIONAL]
        return self._enabledFeatures[feature]

    def _useMemorySpecialization(self):
        usedSpecialization = self._enabledFeaturesUseSpecialization()
        return usedSpecialization

    def _getReversiSIMDMode(self):
        if V_MUTABLE in self._reverseInstructions:
            return V_MUTABLE
        else:
            return self._enabledFeatures[SIMD]

    def _getDefaultReversiSIMDMode(self):
        if V_MUTABLE in self._reverseInstructions:
            return V_MUTABLE
        else:
            return list(self._reverseInstructions.keys())[0]

    def _setOperationRegister(self, operandAttributes):
        self.operandAttributes = operandAttributes
        for instr in self._modInstructions:
            instr.resetFeatures()
            if instr.getName().lower() in self.validInstructionList:
                instr.setFeatures(self._enabledFeatures)
            instr.setOperands(self.operandAttributes)
        for instr in self._sequenceInstructions:
            instr.resetFeatures()
            if instr.getName().lower() in self.validInstructionList:
                instr.setFeatures(self._enabledFeatures)
            instr.setOperands(self.operandAttributes)
        for instr in self.iCacheRepetition:
            instr.resetFeatures()
            if instr.getName().lower() in self.validInstructionList:
                instr.setFeatures(self._enabledFeatures)
            instr.setOperands(self.operandAttributes)

    def _setReverseRegister(self, simdMode, operandAttributes):
        self.operandAttributes = operandAttributes
        for rev_instr in self._reverseInstructions[simdMode]:
            rev_instr.resetFeatures()
            if rev_instr.getName().lower() in self.validInstructionList:
                rev_instr.setFeatures(self._enabledFeatures)
            rev_instr.setOperands(self.operandAttributes)
            rev_instr.setOverrideTargetOperand(self.interleavingTargetRegister)

    def __str__(self):
        description = ""
        for original in self._modInstructions:
            description += original.string()
            description += "\n"
        description += " ->\n"

        for reverse in self._reverseInstructions[self._getReversiSIMDMode()]:
            description += reverse.string()
            description += "\n"
        return description

    def string(self) -> str:
        return self.__str__()

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self._modInstructions == other._modInstructions and self._reverseInstructions == other._reverseInstructions and self._sequenceInstructions == other._sequenceInstructions

    def setGlobalMandatoryFeatures(self, globalMandatoryFeatures):
        self.globalMandatoryFeatures = globalMandatoryFeatures

    def getInstructionCount(self):
        """
        Note: Only works after generating the code!
        :return: number of instructions generated from this testinstruction
        """
        if self._enabledFeaturesUseSpecialization():
            specializedTestInstruction: TestInstruction = self._getSpecializationTestInstruction()
            self.instructionCount = specializedTestInstruction.getInstructionCount()
        return self.instructionCount

    def calculateEnabledInstructions(self, standardReversi=True, sequence=False, sequenceHole=False):
        """
        Estimation of the Instruction Count of a modification and reversing operation.
        Works before code is generated!!!!!!!!!!!!!
        :return:
        """
        self.generateCode = False
        if standardReversi:
            self.generateModificationCode()
            self.generateReversiCode()
            if sequence:
                self.generatePreSequenceCode()
                self.generateSequenceCode()
                self.generatePostSequenceCode()
        elif sequenceHole:
            self.generateModificationCode()
            self.generateSequenceCode()

        self.generateCode = True
        instr = self.getInstructionCount()
        self._resetInstructionCount()
        return instr

    def _resetInstructionCount(self):
        self.instructionCount = 0
        if self._enabledFeaturesUseSpecialization():
            specializedTestInstruction: TestInstruction = self._getSpecializationTestInstruction()
            specializedTestInstruction._resetInstructionCount()

    def _isReadConditionEnabled(self):
        if CONDITIONAL in self._enabledFeatures:
            return CONDITIONAL_READ == self._enabledFeatures[CONDITIONAL]
        else:
            return False

    def _generateInstructionListAssembly(self, instructionList, globalMandatoryFeatures={},
                                         hasOverridingTargetRegister=False):
        if len(list(self.operandAttributes.keys())) == 0:
            # instruction counting, operands have not been set
            if instructionList:
                self.instructionCount += len(instructionList)
            return ""
        else:
            # code generation, operands have been set
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
            instructionList = conditionalExec.getPostReverse(self._enabledFeatures[SIMD], conditionFlag=conditionFlag)
            return self._generateInstructionListAssembly(instructionList, hasOverridingTargetRegister=True) + "\n"

        return ""

    def getType(self):
        # if self._isEnabledFeature(IMMEDIATE):
        #     return "I"
        return self.type

    def hasValidSequenceInstruction(self):
        return len(self._sequenceInstructions) > 0

    def getSequenceInstructionCount(self):
        return len(self._sequenceInstructions)

    def hasNewSequenceTargetReg(self):
        return self.newSequenceTargetReg
