# Copyright (c) 2022 Chair for Chip Design for Embedded Computing,
#                    Technische Universitaet Braunschweig, Germany
#                    www.tu-braunschweig.de/en/eis
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
import warnings

import xmltodict
from random import randint, choice, uniform

import Constants
from Constants import *


class Processor:
    class __processorParser:
        def __init__(self):
            self.branchIndex = 0
            # check if file exists
            parse = self.fetch_xml_data(Constants.PATH_PROCESSOR)
            self._setInstructionXML()
            self.proc_infos = parse[PROCESSOR]

            # Blocked registers
            self._blocked_registers = []

            # parse configurations from xml
            # Set register
            if isinstance(self.proc_infos[REGISTER_FILE], dict):
                self.register = dict(self.proc_infos[REGISTER_FILE])
                self.blockHardRegister()
            else:
                self.register = {}

            # Set issue slots
            if isinstance(self.proc_infos[ISSUE_SLOT], dict):
                self.issue_slots = dict(self.proc_infos[ISSUE_SLOT])
            else:
                self.issue_slots = {}

            # Set assembly structure
            if isinstance(self.proc_infos[ASSEMBLY_STRUCTURE], dict):
                self.assembly_structure = dict(self.proc_infos[ASSEMBLY_STRUCTURE])
            else:
                self.assembly_structure = {}

            # Set immediate
            if isinstance(self.proc_infos[IMMEDIATE], dict):
                self.immediate = dict(self.proc_infos[IMMEDIATE])
            else:
                self.immediate = {}

            # Set immediate operand
            if isinstance(self.proc_infos[IMMEDIATE_OPERAND], dict):
                self.immediate_operand = dict(self.proc_infos[IMMEDIATE_OPERAND])
            else:
                self.immediate_operand = {}


            if isinstance(self.proc_infos[SATURATION], dict):
                self.saturation = dict(self.proc_infos[IMMEDIATE_OPERAND])
            else:
                self.saturation = {}


            self.setMemoryRange()
            n=3

        def __getKeyValue(self, xmlDictionary, key):
            value = xmlDictionary[key]
            if value is None:
                value = ""
            return value


        def setMemoryRange(self):
            self.memory_description = {}
            self.blockedMemoryAddresses = []
            key = PROCESSOR_MEMORY_KEYWORD
            if isinstance(self.proc_infos[key], dict):
                # get start and end addresses
                for memoryDescription in MEMORY_DESCRIPTION:
                    if memoryDescription.value in self.proc_infos[key]:
                        self.memory_description[memoryDescription.value] = int(self.proc_infos[key][memoryDescription.value])

                #get formating information
                self.memory_description[FORMAT] = self.__getKeyValue(self.proc_infos[key], FORMAT)
                for formating in FORMAT_DESCRIPTION:
                    if formating.value in self.proc_infos[key]:
                        value = self.__getKeyValue(self.proc_infos[key], formating.value)
                        self.memory_description[formating.value] = value


        def _setInstructionXML(self):
            self.instructionXML  = self.fetch_xml_data(PATH_INSTRUCTION)[INST_LIST]



        def fetch_xml_data(self, dest: str):
            file = open(dest)
            xml_content = xmltodict.parse(file.read())
            file.close()
            return xml_content

        def blockHardRegister(self):
            if BLOCKED_REGISTER in  self.register:
                for i in range(len(self.register[BLOCKED_REGISTER][REGISTER_FILE])):
                    self._blocked_registers.append([int(self.register[BLOCKED_REGISTER][REGISTER_FILE][i]),
                                                    int(self.register[BLOCKED_REGISTER][REGISTER][i])])

        def getInstructionXML(self):
            return self.instructionXML



    instance = None

    def __init__(self):
        if not Processor.instance:
            Processor.instance = Processor.__processorParser()

    def describe_proc(self) -> str:
        """Helper function to read xml structure"""
        for k, v in self.instance.__dict__.items():
            print("%s: %s"%(k, str(v)))

    def parseInstruction(self, assembly: str) -> list:
        """return [instruction, registerString]"""
        if isinstance(assembly, dict):
            assembly = assembly['#text']

        temp = assembly.split(" ")
        returnlist = []
        instruction = temp.pop(0)
        returnlist.append(instruction)
        register = " ".join(temp)
        returnlist.append(register)
        return returnlist

    def getMandatoryFeatures(self, assembly):
        if not isinstance(assembly, dict):
            return {}
        return assembly[MANDATORY_FEATURE]

    # For Assembly
    def get_instr_features(self, instruction: str) -> dict:
        inst_xml = self.instance.getInstructionXML()
        if instruction.lower() not in inst_xml:
            return {}
        inst = inst_xml[instruction.lower()] # instruction xml must have the same string with inst name, but lower case.

        if instruction is None:
            return self._getDefaultInstructionFeature(inst)
        else:
            return self.append_instr_feature(inst)

    def _getDefaultInstructionFeature(self, inst):
        attr_dict = {}
        for key in inst:
            print(key)
            value= inst[key].split(DELIMITER_FEATURE) if inst[key] is not None else [None]
            if key == ISSUE_SLOT:
                value_update = []
                for v in value:
                    value_update.append(int(v))
                value = value_update
            attr_dict[key] = value


        for attr_list in attr_dict.values():
            for ind, value in enumerate(attr_list):
                if value == '':
                    attr_list[ind] = None

        return attr_dict

    def getFeatureValue(self, enabledFeature, instr_value) -> str:
        if instr_value == None:
            return
        if enabledFeature == SIMD:
            return self.instance.proc_infos[SIMD][instr_value]

        if enabledFeature == SIGNAGE:
            if instr_value == SIGNED:
                return self.instance.proc_infos[SIGNAGE][SIGNED]
            if instr_value == UNSIGNED:
                return self.instance.proc_infos[SIGNAGE][UNSIGNED]

        if enabledFeature == CONDITIONAL:
            if instr_value == COND_SET:
                return self.instance.proc_infos[CONDITIONAL][COND_SET]
            if instr_value == COND_READ:
                return self.instance.proc_infos[CONDITIONAL][COND_READ]
            if instr_value == COND_READ_SET:
                return self.instance.proc_infos[CONDITIONAL][COND_READ_SET]

        if enabledFeature == SATURATION:
            if instr_value == PROCESSOR_DESCRIPTION_SATURATION.overflow.value:
                return self.instance.proc_infos[SATURATION][instr_value]
            if instr_value == PROCESSOR_DESCRIPTION_SATURATION.saturation.value:
                return self.instance.proc_infos[SATURATION][instr_value]

        if enabledFeature == IMMEDIATE:
            if instr_value in self.instance.proc_infos[IMMEDIATE]:
                return self.instance.proc_infos[IMMEDIATE][instr_value]


    def getFeature(self, key, index, instrStr:str = None):
        features = self.getAvailableInstructionFeatures(instrStr)
        try:
            return self.getAvailableInstructionFeatures(instrStr)[key][index]
        except:
            m=3

    def getAvailableInstructionFeatures(self, instruction: str =None) -> dict:
        """ return available features supported by the instruction"""
        if instruction is None:
            instr_attr = self.get_instr_features(INSTRUCTION_DEFAULT_MODES)
        else:
            instr_attr = self.get_instr_features(instruction)

        # Make all possible features
        # features = {}

        for enabledFeature in instructionFeatureList:
            if enabledFeature not in instr_attr:
                instr_attr[enabledFeature] = [None]
            # features[enabledFeature] = []
            # special case handling of features
            # if enabledFeature ==ISSUE_SLOT:
            #     if DEFAULT in self.instance.issue_slots:
            #         features[ISSUE_SLOT].append(self.instance.issue_slots[DEFAULT])
            #     for i in range(int(self.instance.issue_slots[MAX_SIZE])):
            #         features[ISSUE_SLOT].append(i)
            # else: # default handling of features
            #     for value in self.instance.proc_infos[enabledFeature].values():
            #         features[enabledFeature].append(value)

        for enabledFeature in instructionSpecialFeature: # For features that are instruction dependent
            if enabledFeature not in instr_attr:
                instr_attr[enabledFeature] = [None]

            # features[enabledFeature] = []
            # for value in instr_attr[enabledFeature]:
            #     real_value = self.getFeatureValue(enabledFeature, value)
            #     features[enabledFeature].append(real_value)

        return instr_attr

    def random_enabled_features(self, instruction, probability = 0) -> dict:
        """set features to be randomized or not"""

        features = self.getAvailableInstructionFeatures(instruction)

        feature_stats = {}
        for key in features:
            feature_stats[key] = features[key][randint(0, len(features[key]) - 1)]

        if IMMEDIATE in features:
            if features[IMMEDIATE] != [None]:
                rand_prob = round(uniform(0, 1), 3)

                # special handling of immediate Feature
                if rand_prob <= probability:
                   feature_stats[IMMEDIATE] = features[IMMEDIATE][-1]
                else:
                   feature_stats[IMMEDIATE] = None
            else:
                feature_stats[IMMEDIATE] = None

        # warnings.warn("Condition is disabled for now!")
        if CONDITIONAL in features:
            if len(features[CONDITIONAL]) > 1:
                conditionSelected = randint(0, len(features[CONDITIONAL]) - 1)
                conditionValue = self.getAssemlby2Feature(features[CONDITIONAL][conditionSelected])

                # todo: remove constraint
                if COND_SET == conditionValue:
                    if instruction in TEMPORARY_CONDSEL_ENABLED:
                        feature_stats[CONDITIONAL_READ] = "zero"
                        feature_stats[SIMD] = "8"
                    else:
                        conditionSelected = None
                elif CONDITIONAL_READ == conditionValue:
                    condition = randint(0, len(CONDITION_ELEMENTS) - 1)
                    feature_stats[CONDITIONAL_READ] = CONDITION_ELEMENTS[condition]

                feature_stats[CONDITIONAL] = features[CONDITIONAL][conditionSelected]
            else:
                feature_stats[CONDITIONAL] = None


            # # todo: remove constraints
            # if instruction in TEMPORARY_CONDSEL_ENABLED:
            #     conditionSelected = randint(0, len(features[CONDITIONAL])-1)
            #     if "CS" == features[CONDITIONAL][conditionSelected]:
            #         feature_stats[CONDITIONAL_READ] = "zero"
            #         feature_stats[SIMD] = "8"
            #     elif "CR" == features[CONDITIONAL][conditionSelected]:
            #         condition = randint(0, len(CONDITION_ELEMENTS)-1)
            #         feature_stats[CONDITIONAL_READ] = CONDITION_ELEMENTS[condition]
            #         n=3
            #     feature_stats[CONDITIONAL] = features[CONDITIONAL][conditionSelected]
            # else:
            #     feature_stats[CONDITIONAL] = None
        else:
            n=3

        # TODO: remove this line, cond beschäftigen, jz immer noch falsch
        #feature_stats[CONDITIONAL] = 0
        return feature_stats

    def getInstructionAssemblyString(self, name, enabledFeatures) -> str:
        """Get Assembly format in XML then write all features enabled."""
        if not enabledFeatures:
            return name
        returnString = ""
        tempdict = {}

        # Write all features
        for key in self.instance.assembly_structure:
            if key in enabledFeatures:
                tempdict[key] = enabledFeatures[key]
            if INSTRUCTION in key:
                tempdict[key] = str(name)
            if SPACE in key:
                tempdict[key] = " "
            if CONDITIONAL_DELIMITER in key:
                tempdict[key] = ""

        # --Conditions--
        # For Issue slot
        if ISSUE_SLOT in tempdict:
            if isinstance(tempdict[ISSUE_SLOT], int):
                tempdict[ISSUE_SLOT] = ':' + str(tempdict[ISSUE_SLOT])
            elif not tempdict[ISSUE_SLOT]:
                tempdict[SPACE] = ""


        # If instruction already have _xx then dont put conditional things
        if ('_' in tempdict[INSTRUCTION]):
            tempdict[SIGNAGE] = ""
            tempdict[SIMD] = ""

        # For Conditional Delimiter
        tempdict_keys = list(tempdict.keys())
        temp = 0

        ## Find index of CONDITIONAL_DELIMITER
        for key in tempdict_keys:
            if key == CONDITIONAL_DELIMITER:
                temp = tempdict_keys.index(key)
                continue

        ## If after cond_delimiter there's no value then no '_'
        for key in tempdict_keys:
            index = tempdict_keys.index(key) if tempdict[key] else 0
            if index > temp:
                tempdict[CONDITIONAL_DELIMITER] = "_"

        # Add all dict to string then return
        for key in tempdict:
            if tempdict[key]:
                returnString += str(tempdict[key])

        return returnString

    # For Operands
    def get_register_rule(self) -> dict:
        # Get max register eigenschaft
        self.reg_features = {}

        # Make num reg files
        self.reg_features[NUM_REG_FILES] = int(self.instance.register[NUM_REG_FILES])-1

        # Make reg file size
        self.reg_features[REG_FILE_SIZE] = int(self.instance.register[REG_FILE_SIZE])-1

        # Make reg format
        self.reg_features[FORMAT] = self.instance.register[FORMAT]

        return self.reg_features

    def get_immediate_operand_rule(self) -> dict:
        return self.instance.immediate_operand

    def create_register_operand(self, bank: int = 0, register: int = 0) -> str:
        """Create register string by modifying format str"""
        self.reg_format = self.get_register_rule()[FORMAT]
        self.reg_format = self.reg_format.replace('_regFile_', str(bank))
        self.reg_format = self.reg_format.replace('_register_', str(register))

        return self.reg_format

    def create_immediate_operand(self, value: int = 0, type: str = DEC) -> str:
        # Make immediate operand
        imm_rule = self.get_immediate_operand_rule()
        imm_format = imm_rule[FORMAT]

        # immediate type setting
        if imm_rule[type] == None:
            imm_type = ''
        else:
            imm_type = imm_rule[type]

        #convert value
        if type == DEC:
            imm_value = str(value)
        else:
            imm_value = self.convert_number(value, type)

        imm_format = imm_format.replace('_x_', str(imm_type))
        imm_format = imm_format + imm_value

        return imm_format

    def convert_number(self, value: int = 0, type: str = BIN) -> str:
        # value is always dec
        # Convert bin
        if type == BIN:
            return_value = '{:b}'.format(value)
            return return_value
        elif type == HEX:
            return_value = '{:x}'.format(value)
            return return_value
        else:
            #error
            return ERROR

    def getOperandTypes(self, operandstring: str, enabledfeatures: dict) -> dict:
        # Make dict of operand types.
        # Make dict of operand types.
        oplist = operandstring.split(', ')
        opdict = {key: OPERAND_TYPE.Register for key in oplist}
        if enabledfeatures[IMMEDIATE]:
            last = list(opdict)[-1]
            opdict[last] = OPERAND_TYPE.Immediate

        return opdict

    def getDefaultOperandType(self, enabledfeatures: dict) -> dict:
        # Make dict of operand types.
        opdict = {}
        for operand in OPERANDS:
            opdict[operand.value] = OPERAND_TYPE.Register

        # if enabledfeatures[IMMEDIATE]:
        opdict[OPERANDS.RAND_IMMEDIATE.value] = OPERAND_TYPE.Immediate

        # the ordering is important for the correct replacement strategy in assembly
        opdict[OPERANDS.ADDRESS4.value] = OPERAND_TYPE.Address4
        opdict[OPERANDS.ADDRESS3.value] = OPERAND_TYPE.Address3
        opdict[OPERANDS.ADDRESS2.value] = OPERAND_TYPE.Address2
        opdict[OPERANDS.ADDRESS.value] = OPERAND_TYPE.Address
        opdict[OPERANDS.BRANCH_INDEX.value] = OPERAND_TYPE.BRANCH_INDEX

        return opdict

    def generate_random_operand(self, type: str, enabledfeatures: dict, block: bool = False) -> str:
        # If type is register do:
        if type == OPERAND_TYPE.Register:
            max_reg_file = int(self.get_register_rule()[NUM_REG_FILES])
            max_reg_size = int(self.get_register_rule()[REG_FILE_SIZE])
            self.use_register = self.create_use_register(max_reg_file, max_reg_size)
            self.check = True
            while self.check:
                if self.use_register not in self.instance._blocked_registers:
                    if block:
                        self.instance._blocked_registers.append(self.use_register)
                    self.check = False
                    self.reg_operand = self.create_register_operand(bank= self.use_register[0],
                                                                    register= self.use_register[1])
                    return self.reg_operand
                else:
                    self.use_register = self.create_use_register(max_reg_file, max_reg_size)

        # If type is immediate do:
        elif type == OPERAND_TYPE.Immediate:
            return self.create_rand_immediate(enabledfeatures)
        elif type == OPERANDS.ADDRESS:
            return self.createRandomMemoryAddress()

    def createRandomMemoryAddress(self):
        start =0
        end = DEFAULT_MAX_MEMORY_ADDRESS
        if MEMORY_DESCRIPTION.startAddress.value in self.instance.memory_description:
            start = self.instance.memory_description[MEMORY_DESCRIPTION.startAddress.value]
        if  MEMORY_DESCRIPTION.endAddress.value in self.instance.memory_description:
            end = self.instance.memory_description[MEMORY_DESCRIPTION.endAddress.value]
        elements = list(range(start, end))
        for blocked in self.instance.blockedMemoryAddresses:
            elements.remove(blocked)
        address = choice(elements)
        self.instance.blockedMemoryAddresses.append(address)
        return address

    def removeMemoryAddress(self, memoryAddress):
        self.instance.blockedMemoryAddresses.remove(memoryAddress)

    def get_operands_string(self, operandstrings: str, enabledfeatures: dict) -> str:
        # Make random operand
        self.reg_features = self.get_register_rule()
        self.imm_features = self.get_immediate_operand_rule()
        optypes = self.getOperandTypes(operandstrings, enabledfeatures)

        # Make Operands
        oplist = [self.generate_random_operand(typ, enabledfeatures) for typ in optypes]


        returnstring = ", ".join(oplist)
        return returnstring

    def generateRandomOperands(self, enabledfeatures, generateFocusRegister=True, FocusRegister=None):
        operands = self.getDefaultOperandType(enabledfeatures)
        # special case Handling of Rand Value
        if generateFocusRegister:
            operands[OPERANDS.FOCUS_REGISTER.value] = self.generateRandomOperand(operands[OPERANDS.FOCUS_REGISTER.value], enabledfeatures, block=True)
        operands[RAND_VALUE] = self.generateRandomOperand(operands[RAND_VALUE], enabledfeatures, block=True)
        for key in operands:
            block = False
            if not generateFocusRegister and OPERANDS.FOCUS_REGISTER.value == key:
                continue
            if generateFocusRegister and OPERANDS.FOCUS_REGISTER.value == key:
                # block first focus register of interleaving sequence
                continue

            if key ==  RAND_VALUE:
                continue
            operands[key] = self.generateRandomOperand(operands[key], enabledfeatures, block=block)
        while self.isRegisterConflict(operands, FocusRegister):
            operands[RAND_VALUE] = self.generateRandomOperand(OPERAND_TYPE.Register, enabledfeatures, block=True)
            operands[OPERANDS.TARGET_REGISTER.value] = self.generateRandomOperand(OPERAND_TYPE.Register, enabledfeatures, block=False)
        return operands

    def isRegisterConflict(self, operands, FocusRegister=None):
        value =  (FocusRegister == operands[RAND_VALUE]) or (FocusRegister == operands[OPERANDS.TARGET_REGISTER.value])
        return value

    def generateRandomOperand(self, type, enabledFeatures, block=False):
        # If type is register do:
        if type == OPERAND_TYPE.Register:
            max_reg_file = int(self.get_register_rule()[NUM_REG_FILES])
            max_reg_size = int(self.get_register_rule()[REG_FILE_SIZE])
            use_register = self.create_use_register(max_reg_file, max_reg_size)
            self.check = True
            while self.check:
                if use_register not in self.instance._blocked_registers:
                    if block:
                        self.instance._blocked_registers.append(use_register)
                    self.check = False
                    reg_operand = self.create_register_operand(bank=use_register[0],
                                                                    register=use_register[1])

                    return reg_operand
                else:
                    use_register = self.create_use_register(max_reg_file, max_reg_size)

        # If type is immediate do:
        elif type == OPERAND_TYPE.Immediate:
            return  self.create_rand_immediate(enabledFeatures)
        elif type == OPERAND_TYPE.Address:
            return self.createRandomMemoryAddress()
        elif type == OPERAND_TYPE.Address2:
            return self.createRandomMemoryAddress()
        elif type == OPERAND_TYPE.Address3:
            return self.createRandomMemoryAddress()
        elif type == OPERAND_TYPE.Address4:
            return self.createRandomMemoryAddress()
        elif type == OPERAND_TYPE.BRANCH_INDEX:
            self.instance.branchIndex +=1
            return self.instance.branchIndex

    def getOperandAssembly(self, operandString :str, operandAttributes: dict, overridingTargetRegister=None, isPragma=False, isRandValueRandomImmediate=False):
        """

        :param operandString:
        :param operandAttributes:
        :param overridingTargetRegister:
        :param isPragma:
        :param isRandValueRandomImmediate: Only modifying operation needs to replace randValue with Immidiate, other is false
        :return:
        """
        operandParts = operandString.replace(",", "").split(" ")
        operandParts = [str(i) for i in operandParts]
        for operand, value in operandAttributes.items():
            if operand is TARGET_REGISTER:
                if overridingTargetRegister is not None:
                    value = overridingTargetRegister

            if isRandValueRandomImmediate and operand == RAND_VALUE:
                value = operandAttributes[OPERANDS.RAND_IMMEDIATE.value]

            if operand == OPERANDS.RAND_IMMEDIATE.value:
                value = operandAttributes[OPERANDS.RAND_IMMEDIATE.value]

            while operand in operandParts:
                index = operandParts.index(operand)
                operandParts[index] = str(value)



            operandString = operandString.replace(operand, str(value))

        if isPragma:
            operandResult = " ".join(operandParts)
        else:
            operandResult = ", ".join(operandParts)

        operandResult = self.replacePartialOperands(operandResult, operandAttributes)

        return operandResult

    def generate_ComparisonCode(self, instr_list : list, focusInstruction, targetInstruction) -> str:
        comparison_code = ''
        for instr in instr_list:
            instr = instr.replace(FOCUS_REGISTER, focusInstruction.getFocusOperand())
            instr = instr.replace(TARGET_REGISTER, targetInstruction.getTargetOperand())
            comparison_code += str(instr)
            comparison_code += '\n'
        return comparison_code



    def replacePartialOperands(self, operandResult, operandAttributes):
        if operandAttributes :

            for keyword in ASSEMBLY_PARTIAL:
                if keyword.value in operandResult:
                    operandValue = str(operandAttributes[keyword.value])
                    operandResult = operandResult.replace(keyword.value, operandValue)

        return operandResult

    def isPragma(self, instructionString):
        for keyword in ASSEMBLY_PRAGMAS:
            if keyword.value in instructionString:
                return True
        return False

    def create_use_register(self, max_reg_file, max_reg_size):
        return [randint(0, max_reg_file), randint(0, max_reg_size)]

    def create_rand_immediate(self, enabledfeatures):
        immediate_String = enabledfeatures[IMMEDIATE]
        return self.createRandImmediate(immediate_String)

    def createRandImmediate(self, immediateString):
        # try:
        #     immediateString = Processor().getAvailableInstructionFeatures()[IMMEDIATE][immediateString]
        # except:
        #     n=3
        for k, v in self.instance.immediate.items():
            if v == immediateString:
                if k == DEFAULT:
                    imm_type = PROCESSOR_DESCRIPTION_IMMEDIATE.short.value
                else:
                    imm_type = k


        max_value = int(self.get_immediate_operand_rule()[imm_type])
        val = randint(0, max_value)
        imm_basis =  HEX
        reg_operand = self.create_immediate_operand(val, imm_basis)
        return reg_operand

    def append_instr_feature(self, inst):
        attr_dict = {}
        for feature in instructionFeatureList:
            if feature in inst:
                attr_dict[feature] = inst[feature].split(DELIMITER_FEATURE) if inst[feature] is not None else [None]
            else:
                attr_dict[feature] = [None]

        for feature in instructionSpecialFeature:
            if feature in inst:
                attr_dict[feature] = inst[feature].split(DELIMITER_FEATURE) if inst[feature] is not None else [None]
            else:
                attr_dict[feature] = [None]


        for attr_list in attr_dict.values():
            for ind, value in enumerate(attr_list):
                if value == '':
                    attr_list[ind] = None

        feature  = {}
        # convert value to Assembly
        for key in attr_dict:
            feature[key] = []
            for value in attr_dict[key]:
                if value == 'None' or value is None:
                    feature[key].append(None)
                else:
                    try:
                        feature[key].append(self.instance.proc_infos[key][value])
                    except:
                        n=3

        return feature

    def getRandomIssueSlot(self):
        return randint(0, int(self.instance.issue_slots[MAX_SIZE]));

    def getBlockedRegister(self):
        return self.instance._blocked_registers

    def getSIMD(self):
        return self.instance.proc_infos[SIMD]

    def resetBlockedRegister(self):
        self.instance._blocked_registers = []
        self.instance.blockHardRegister()
        n=3

    def resetBranchIndex(self):
        self.instance.branchIndex =0

    def reset(self):
        self.resetBlockedRegister()
        self.resetBranchIndex()
        self.instance.blockedMemoryAddresses = []

    def getProcessorFeatureAssembly(self, feature, value):
        # if feature == CONDITIONAL:
        #     return self.instance.proc_infos[CONDITIONAL_VALUES][value]
        assembly = self.instance.proc_infos[feature][value]
        if not assembly :
            return value
        else:
            return assembly



    def getProcessorFeatureList(self, feature):
        return self.instance.proc_infos[feature]

    def getAssemlby2Feature(self, assembly):

        if assembly:

            for instrFeature in instructionSpecialFeature:
                for key, value in self.instance.proc_infos[instrFeature].items():
                    if value:
                        if assembly in value:
                            return key


            for instrFeature in instructionFeatureList:
                for key, value in self.instance.proc_infos[instrFeature].items():
                    if assembly in key:
                        return value
        else:
            return None


