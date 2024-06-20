import copy
import warnings

from Constants import OPERANDS
from util.Processor import Processor

class Instruction:

    def __init__(self, assembly: str, instruction_set, mutable=True):
        # set default enabled features
        self.isRandValueRandomImmediate = False
        self.globalMandatoryFeatures = {}
        self.mutable = mutable
        self._assembly = assembly
        self.parsestring = Processor().parseInstruction(assembly)

        self.mandatoryEnabledFeatures = Processor().getMandatoryFeatures(assembly)
        self.inst_name = self.parsestring[0]
        # if instruction is already modified, then it is not mutable (i.e. MVIL_32)
        self._is_instruction_mutable(instruction_set)

        self.features = self.getFeatures()
        self._enabledfeatures = {}

        # Operands
        self._operandAttr = {}  # TARGET_REGISTER, FOCUS_REGISTER, RAND_VALUE

        # parse assembly for return
        self._instruction = self.parsestring[0]
        self._operandStrings = self.parsestring[1]
        self._originalOperandString = copy.deepcopy(self.parsestring[1])
        self.interleavingTargetRegister = None
        
        # parse immediate features
        self.allows_immediate = self.parsestring[1].split(",")[-1].strip() == OPERANDS.RAND_VALUE.value
    
    def _is_instruction_mutable(self, instruction_list):
        if self.mutable:
            if self.inst_name.startswith("--"):
                self.mutable = False
            elif any(x in self.inst_name for x in Processor().get_delimiter_list()):
                self.mutable = False
            elif any([self.inst_name.lower().endswith(x) for x in Processor().get_immediate_assembly()]):
                # check if instruction ends with I or IL (also not mutable)
                try:
                    found_base_instruction = Processor().find_base_instruction(self.inst_name, instruction_list)
                    self.mutable = found_base_instruction == self.inst_name
                except Exception as e:
                    warnings.warn(f"Instruction {self.inst_name} not found in instruction list")
                    self.mutable = False
                    
            

                
                

    def getFeatures(self):
        instructionName = None
        if len(self.parsestring) > 2:
            instructionName = self.inst_name
        try:
            features = Processor().getAvailableInstructionFeaturesNames(instructionName)
            # overwrite mandatory features
            for feature in self.mandatoryEnabledFeatures:
                features[feature] = self.mandatoryEnabledFeatures[feature]

            return features
        except KeyError:
            return None

    def get_operand_attr(self):
        return self._operandAttr

    def get_enabled_features(self):
        return self._enabledfeatures

    def setFeatures(self, features):
        """
        Reset all features and set them new.
        :param features: to set of the instruction.
        :return:
        """
        self._enabledfeatures = {}
        availableFeatures = Processor().getAvailableInstructionFeaturesNames(self.inst_name)

        for key in features:
            if key in availableFeatures:
                FeatureName = features[key]
                if FeatureName in availableFeatures[key]:
                    self._enabledfeatures[key] = FeatureName
        self._setInstructionAssembly()

    def getOperandAssembly(self):  # in processor
        return Processor().getOperandAssembly(self.parsestring[1], self._operandAttr, self.interleavingTargetRegister,
                                              isRandValueRandomImmediate=self.isRandValueRandomImmediate)

    def replaceRegisterTemplate(self, oldReg, newReg):
        """
        Use with extreme caution. This will overwrite the instruction Template.
        :param oldReg:
        :param newReg:
        :return:
        """
        self.parsestring[1] = self.parsestring[1].replace(oldReg, newReg)

    def __str__(self) -> str:
        self._setInstructionAssembly()
        return self._instruction + " " + self.getOperandAssembly()

    def string(self) -> str:
        return self.__str__()

    def getName(self) -> str:
        return self.inst_name

    def getAssembly(self, enabledFeatures, globalMandatoryFeatures={}):
        self.setFeatures(enabledFeatures)
        self.setGlobalMandatoryFeatures(globalMandatoryFeatures)
        return self.string()

    def setEnabledFeatures(self, key: int, value: int):
        self._enabledfeatures[key] = value

        self._setInstructionAssembly()

    def set_default_feature_values(self):
        if self.features is None:
            return
        for key in self.features:
            self._enabledfeatures[key] = self.features[key][0]
        self._setInstructionAssembly()

    def _setInstructionAssembly(self):
        if self.mutable:
            self.overrideMandatoryFeatures()
            self._instruction = Processor().getInstructionAssemblyString(self.parsestring[0],
                                                                         self._enabledfeatures)
        # else:
        #     # Issue slot will always be set, even if instruction is not mutable!
        #     self.overrideMandatoryFeatures()
        #     self._instruction = Processor().get_issue_slot_string(self._enabledfeatures) + self._instruction
            

        if OPERANDS.BRANCH_INDEX.value in self._instruction:
            if OPERANDS.BRANCH_INDEX.value in self._operandAttr:
                self._instruction = self._instruction.replace(OPERANDS.BRANCH_INDEX.value,
                                                              str(self._operandAttr[OPERANDS.BRANCH_INDEX.value]))

    def overrideMandatoryFeatures(self):
        for feature in self.mandatoryEnabledFeatures:
            self._enabledfeatures[feature] = self.mandatoryEnabledFeatures[feature]
        for key in self.globalMandatoryFeatures:
            if key in self._enabledfeatures and key in self.mandatoryEnabledFeatures:
                self._enabledfeatures[key] = self.globalMandatoryFeatures[key]

    def setGlobalMandatoryFeatures(self, globalMandatoryFeature):
        self.globalMandatoryFeatures = globalMandatoryFeature

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.__str__() == other.__str__()

    def setOperands(self, operands):
        self._operandAttr = operands

    def setOverrideTargetOperand(self, overRidingTargetOperand):
        self.interleavingTargetRegister = overRidingTargetOperand

    def enableRandValueRandomImmediate(self):
        self.isRandValueRandomImmediate = True

    def getRawAssembly(self):
        return self._assembly
    
    def has_allows_immediate(self):
        return self.allows_immediate
        
