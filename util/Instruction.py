import copy
import warnings

from Constants import TARGET_REGISTER, RAND_VALUE, FOCUS_REGISTER, ADDRESS, OPERAND_TYPE, OPERANDS, ISSUE_SLOT
from util.Processor import Processor


class Instruction:

    def __init__(self, assembly: str, mutable=True):
        # set default enabled features
        self.isRandValueRandomImmediate = False
        self.globalMandatoryFeatures = {}
        self.mutable = mutable
        self._assembly = assembly
        self.parsestring = Processor().parseInstruction(assembly)


        self.mandatoryEnabledFeatures = Processor().getMandatoryFeatures(assembly)
        self.inst_name = self.parsestring[0]

        self.features = self.getFeatures()
        self._enabledfeatures = {}
        # self.reset_features()

        # Operands
        self._operandAttr = {}  # TARGET_REGISTER, FOCUS_REGISTER, RAND_VALUE

        # parse assembly for return
        self._instruction = self.parsestring[0]
        self._operandStrings = self.parsestring[1]
        self._originalOperandString = copy.deepcopy(self.parsestring[1])
        self.interleavingTargetRegister = None

    def getFeatures(self):
        instructionName = None
        if len(self.parsestring) > 2:
            instructionName = self.inst_name
        try:
            features  = Processor().getAvailableInstructionFeatures(instructionName)
            # overwrite mandatory features
            for feature in self.mandatoryEnabledFeatures:
                features[feature] = [Processor().getFeatureValue(feature, self.mandatoryEnabledFeatures[feature])]
            return features
        except KeyError:
            return None

    def get_operand_attr(self):
        return self._operandAttr

    def getEnabledFeatures(self):
        return self._enabledfeatures

    def setFeatures(self, features):
        """
        Reset all features and set them new.
        :param features: to set of the instruction.
        :return:
        """
        self._enabledfeatures = {}
        availableFeatures = Processor().getAvailableInstructionFeatures(self.inst_name)
        # self._enabledfeatures = features
        for key in features:
            if key in availableFeatures:
                assemblyFeatureString = features[key]
                if assemblyFeatureString in availableFeatures[key]:
                    self._enabledfeatures[key] = assemblyFeatureString

        self._setInstructionAssembly()




    def getOperandAssembly(self):  # in processor
        isPragma = Processor().isPragma(self.inst_name)
        # v = Processor().getOperandAssembly(self.parsestring[1], self._operandAttr, self.interleavingTargetRegister, isPragma=isPragma)
        return Processor().getOperandAssembly(self.parsestring[1], self._operandAttr, self.interleavingTargetRegister, isPragma=isPragma, isRandValueRandomImmediate=self.isRandValueRandomImmediate)

    def __str__(self) -> str:
        self._setInstructionAssembly()
        return self._instruction + " " + self.getOperandAssembly()

    def string(self) -> str:
        return self.__str__()

    def getRawString(self):
        return self.inst_name + " " + self._originalOperandString

    def getName(self) -> str:
        return self.inst_name

    def getAssembly(self, enabledFeatures, globalMandatoryFeatures={}):
        self.setFeatures(enabledFeatures)
        self.setGlobalMandatoryFeatures(globalMandatoryFeatures)
        return self.string()

    def setEnabledFeatures(self, key: int, value: int):
        self._enabledfeatures[key] = value
        #if value in self.features[key]:
        #    self._enabledfeatures[key] = value
        #else:
        #    self._enabledfeatures[key] = None

        self._setInstructionAssembly()

    def resetFeatures(self):
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

        if OPERANDS.BRANCH_INDEX.value in self._instruction:
            if OPERANDS.BRANCH_INDEX.value in self._operandAttr:
                self._instruction = self._instruction.replace(OPERANDS.BRANCH_INDEX.value, str(self._operandAttr[OPERANDS.BRANCH_INDEX.value]))
            n=3


    def overrideMandatoryFeatures(self):
        for feature in self.mandatoryEnabledFeatures:
            self._enabledfeatures[feature] = Processor().getFeatureValue(feature, self.mandatoryEnabledFeatures[feature])

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

