# Copyright (c) 2023 Chair for Chip Design for Embedded Computing,
#                    Technische Universitaet Braunschweig, Germany
#                    www.tu-braunschweig.de/en/eis
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import random
from random import randint, uniform, randrange, shuffle
from typing import Dict, List, Union

import xmltodict

from Constants import *


class Processor:
    class __processorParser:

        def __init__(self, architecture, cacheMiss=0.0, newMemoryBlock=0.0):
            self.cacheMiss = cacheMiss
            self.newMemoryBlock = newMemoryBlock
            self.branchIndex = -1
            self.startAddress = -1
            # check if file exists
            self.proc_infos = self.fetch_xml_data(get_path_processor(architecture))[
                PROCESSOR]  # content of processor file
            self.instructionXML = self.fetch_xml_data(get_path_instruction(architecture))[INST_LIST]

            # Blocked registers
            self._blocked_registers = []
            self._ignoreRegister = []  # Registers that should never be used or initialised automaitcly

            # parse configurations from xml
            # Set register
            if isinstance(self.proc_infos[REGISTER_FILE], dict):
                self.register = dict(self.proc_infos[REGISTER_FILE])
                if IMMEDIATE in self.register:
                    self.immediateRegister = [int(self.register[IMMEDIATE][REGISTER_FILE]),
                                              int(self.register[IMMEDIATE][REGISTER])]
                else:
                    self.immediateRegister = None
                self.blockHardRegister()
                self.ignoreRegister()
                self.createRegisterStack()
            else:
                self.register = {}

            # Set issue slots
            if isinstance(self.proc_infos[ISSUE_SLOT], dict):
                self.issue_slots = dict(self.proc_infos[ISSUE_SLOT])
            else:
                self.issue_slots = {}

            # Set assembly structure
            # todo: FIXME: Structure only works if each object only used once. Multiple Delimiters dont work.
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

            self.setMemoryDescription()
            self.branchTargetLabel = ""
            if BRANCH_TARGET in self.proc_infos:
                self.branchTargetLabel = self.proc_infos[BRANCH_TARGET]
            self.maxBranchDistance = -1
            if MAX_BRANCH_DISTANCE in self.proc_infos:
                self.maxBranchDistance = int(self.proc_infos[MAX_BRANCH_DISTANCE])

            self._readCaches()

        def _readCaches(self):
            self.dCacheSpec = {}
            if D_CACHE in self.proc_infos:
                self.dCacheSpec[CACHE_LINES] = int(self.proc_infos[D_CACHE][CACHE_LINES])
                self.dCacheSpec[CACHE_BYTE_PER_LINE] = int(self.proc_infos[D_CACHE][CACHE_BYTE_PER_LINE])
                self.dCacheSpec[CACHE_ASSOCIATION] = int(self.proc_infos[D_CACHE][CACHE_ASSOCIATION])
                self.dCacheSpec[CACHE_WORD_SIZE_BITS] = int(self.proc_infos[D_CACHE][CACHE_WORD_SIZE_BITS])
            self.iCacheSpec = {}
            if I_CACHE in self.proc_infos:
                self.iCacheSpec[CACHE_LINES] = int(self.proc_infos[I_CACHE][CACHE_LINES])
                self.iCacheSpec[CACHE_BYTE_PER_LINE] = int(self.proc_infos[I_CACHE][CACHE_BYTE_PER_LINE])
                self.iCacheSpec[CACHE_ASSOCIATION] = int(self.proc_infos[I_CACHE][CACHE_ASSOCIATION])
                self.iCacheSpec[CACHE_WORD_SIZE_BITS] = int(self.proc_infos[I_CACHE][CACHE_WORD_SIZE_BITS])

        def getNextMemoryAddress(self, dataCache=True):
            cache = self.iCacheSpec
            if dataCache:
                cache = self.dCacheSpec

            prob = random.uniform(0, 1)
            if prob < self.cacheMiss:
                return int(cache[CACHE_BYTE_PER_LINE] * cache[CACHE_LINES])
            else:
                return int(cache[CACHE_WORD_SIZE_BITS] / 8)

        def getIMemJumpInstructions(self):
            cache = self.iCacheSpec
            addressesPerInstruction = cache[CACHE_WORD_SIZE_BITS] / 8
            instructionPerLine = cache[CACHE_BYTE_PER_LINE] / addressesPerInstruction
            return int(instructionPerLine * cache[CACHE_LINES])

        def __getKeyValue(self, xmlDictionary, key):
            value = xmlDictionary[key]
            if value is None:
                value = ""
            return value

        def setMemoryDescription(self):
            """Sets memory range and format description"""
            self.memory_description = {}
            self.blockedMemoryAddresses = []  # Question: why here if blocked Memory is not used?
            key = PROCESSOR_MEMORY_KEYWORD
            if isinstance(self.proc_infos[key], dict):
                # get start and end addresses
                for memoryDescription in MEMORY_DESCRIPTION:
                    if memoryDescription.value in self.proc_infos[key]:
                        if memoryDescription.value == MEMORY_DESCRIPTION.IMEM_OVERLAP.value:
                            self.memory_description[memoryDescription.value] = True
                        else:
                            self.memory_description[memoryDescription.value] = int(
                                self.proc_infos[key][memoryDescription.value])

                # get formating information
                self.memory_description[FORMAT] = self.__getKeyValue(self.proc_infos[key], FORMAT)
                for formating in FORMAT_DESCRIPTION:
                    if formating.value in self.proc_infos[key]:
                        value = self.__getKeyValue(self.proc_infos[key], formating.value)
                        self.memory_description[formating.value] = value

        def fetch_xml_data(self, path: str):
            file = open(path)
            xml_content = xmltodict.parse(file.read())
            file.close()
            return xml_content

        def blockHardRegister(self):

            if BLOCKED_REGISTER in self.register:
                for i in range(len(self.register[BLOCKED_REGISTER][REGISTER_FILE])):
                    self._blocked_registers.append([int(self.register[BLOCKED_REGISTER][REGISTER_FILE][i]),
                                                    int(self.register[BLOCKED_REGISTER][REGISTER][i])])
                if self.immediateRegister:
                    self._blocked_registers.append(self.immediateRegister)

        def ignoreRegister(self):
            """sets _ignoreRegister to a list with all registers that should never be used"""
            if IGNORE_REGISTER in self.register:
                for i in range(len(self.register[IGNORE_REGISTER][REGISTER_FILE])):
                    self._ignoreRegister.append([int(self.register[IGNORE_REGISTER][REGISTER_FILE][i]),
                                                 int(self.register[IGNORE_REGISTER][REGISTER][i])])

        def createRegisterStack(self):
            """Create a new register stack with all possible registers and sets _registerStack. The list is shuffled randomly."""
            max_reg_file = int(self.register[NUM_REG_FILES])
            max_reg_size = int(self.register[REG_FILE_SIZE])

            registerStack = []

            for reg_file in range(max_reg_file):
                for reg_size in range(max_reg_size):
                    if [reg_file, reg_size] not in self._blocked_registers and [reg_file,
                                                                                reg_size] not in self._ignoreRegister:
                        registerStack.append([reg_file, reg_size])

            shuffle(registerStack)
            self._registerStack = registerStack

        def getInstructionXML(self):
            return self.instructionXML

    instance = None

    def __init__(self, architecture="rv32imc", cacheMiss=0.0, newMemoryBlock=0.0):
        if not Processor.instance:
            Processor.instance = Processor.__processorParser(architecture, cacheMiss, newMemoryBlock)

    def parseInstruction(self, assembly: str) -> list:
        """return [instruction, registerString]"""
        if isinstance(assembly, dict):
            assembly = assembly[PLACEHOLDER]

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

    def getBranchTargetLabel(self):
        return self.instance.branchTargetLabel

    # For Assembly
    def get_instr_features(self, instruction: str) -> dict:
        inst_xml = self.instance.getInstructionXML()
        if instruction.lower() not in inst_xml:
            return {}
        inst = inst_xml[
            instruction.lower()]  # instruction xml must have the same string with inst name, but lower case.
        if instruction is None:
            return self._getDefaultInstructionFeature(inst)
        else:
            return self.append_instr_feature(inst)

    def _getDefaultInstructionFeature(self, inst):
        attr_dict = {}
        for key in inst:
            value = inst[key].split(DELIMITER_FEATURE) if inst[key] is not None else [None]
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

    def getFeatureValue(self, feature: str, instrAttribute: str) -> Union[str, None]:
        """returns the assembly code of the instruction attribute wich is part of the feature. Gets the code from the processor description.

        Args:
            feature (str): the feature name wich contains the attribute
            instrAttribute (str): the attribute name to get the assembly code for

        Returns:
            Union[str, None]: the assembly code of the instruction attribute   
        """
        try:
            value = self.instance.proc_infos[feature][instrAttribute]
        except:
            value = None
        return value

    def getFeatureAttributes(self, feature: str) -> Union[list, None]:
        """returens the prossible attributes of a given feature from processor definition

        Args:
            feature (str): the feature name to get the attributes for

        Returns:
            Union[list, None]: the attributes of the feature
        """
        try:
            attributes = self.instance.proc_infos[feature]
        except:
            attributes = []
        return attributes

    def getAvailableInstructionFeaturesNames(self, instruction: str = None) -> dict:
        """gets available instruction features of given instruction name or default. Returns dict of featueres with each possible attribute. Attribute are names, not assembly.

        Args:
            instruction (str, optional): Name of the instruction. Defaults to None.

        Returns:
            dict: Featueres with each possible attribute.
        """
        # get instruction definition
        instruction = instruction if instruction else INSTRUCTION_DEFAULT_MODES
        instXML = self.instance.getInstructionXML()
        if instruction.lower() not in instXML:
            return {}
        inst = instXML[instruction.lower()]  # instruction xml must have the same string with inst name, but lower case.

        attrDict = {}
        for feature in INSTRUCTION_FEATURE_LIST + INSTRUCTION_SPECIAL_FEATURE:
            if feature in inst and inst[feature] is not None:
                attrDict[feature] = inst[feature].split(DELIMITER_FEATURE)
            else:
                attrDict[feature] = [None]

        # change empty string to None
        for attrList in attrDict.values():
            for key, value in enumerate(attrList):
                if value == '' or value == 'None':
                    attrList[key] = None
        return attrDict

    def random_enabled_features(self, instruction, immediateProbability=0.0, switchProbability=0.0) -> dict:
        """set features to be randomized or not"""

        features = self.getAvailableInstructionFeaturesNames(instruction)
        feature_stats = {}
        for key in features:
            feature_stats[key] = features[key][randint(0, len(features[key]) - 1)]
        if IMMEDIATE in features:
            if features[IMMEDIATE] != [None]:
                rand_prob = round(uniform(0, 1), 3)
                # special handling of immediate Feature
                if rand_prob <= immediateProbability or not (None in features[IMMEDIATE]):
                    feature_stats[IMMEDIATE] = features[IMMEDIATE][-1]

                else:
                    feature_stats[IMMEDIATE] = None
            else:
                feature_stats[IMMEDIATE] = None

        # Switch Handling
        if SWITCH in features:
            if features[SWITCH] != [None]:
                rand_prob = round(uniform(0, 1), 3)
                # only use if not immediate
                if rand_prob <= switchProbability and ((IMMEDIATE in feature_stats and feature_stats[
                    IMMEDIATE] == None) or IMMEDIATE not in feature_stats):
                    feature_stats[SWITCH] = "true"

                else:
                    feature_stats[SWITCH] = None
            else:
                feature_stats[SWITCH] = None

        if CONDITIONAL in features:
            if len(features[CONDITIONAL]) > 1:
                conditionSelected = randint(0, len(features[CONDITIONAL]) - 1)

                conditionValue = features[CONDITIONAL][conditionSelected]

                # todo: remove constraint
                # idea: conditional features also defined in instructions?
                if CONDITIONAL_SET == conditionValue:
                    if instruction in TEMPORARY_CONDSEL_ENABLED:
                        feature_stats[CONDITIONAL_READ] = "zero"
                        feature_stats[SIMD] = "8"
                    # else:
                    #     conditionSelected = None
                elif CONDITIONAL_READ == conditionValue:
                    condition = randint(0, len(CONDITION_ELEMENTS) - 1)
                    feature_stats[CONDITIONAL_READ] = CONDITION_ELEMENTS[condition]

                feature_stats[CONDITIONAL] = features[CONDITIONAL][conditionSelected]
            else:
                feature_stats[CONDITIONAL] = None

        return feature_stats

    def getInstructionAssemblyString(self, name, enabledFeatures) -> str:
        """Get Assembly format in XML then write all features enabled."""
        # TODO: remove hard coded structure like ":" for issue slot
        if not enabledFeatures:
            return name
        returnString = ""
        tempdict = {}
        # Write all features
        for key in self.instance.assembly_structure:
            if key in enabledFeatures:
                tempdict[key] = self.getFeatureValue(key, enabledFeatures[key])
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
        temp = -1

        ## Find index of CONDITIONAL_DELIMITER
        # TODO: Only works for one
        for key in tempdict_keys:
            if key == CONDITIONAL_DELIMITER:
                temp = tempdict_keys.index(key)
                continue

        ## If after cond_delimiter there's no value then no '_'
        # Question: is this even right?
        for key in tempdict_keys:
            index = tempdict_keys.index(key)
            if index > temp and temp != -1:
                tempdict[CONDITIONAL_DELIMITER] = "_"

        # Add all dict to string then return
        for key in tempdict:
            if tempdict[key]:
                returnString += str(tempdict[key])

        return returnString

    # For Operands
    def get_register_rule(self) -> dict:
        # Get max register property
        self.reg_features = {}

        # Make num reg files
        self.reg_features[NUM_REG_FILES] = int(self.instance.register[NUM_REG_FILES]) - 1

        # Make reg file size
        self.reg_features[REG_FILE_SIZE] = int(self.instance.register[REG_FILE_SIZE]) - 1

        # Make reg format
        self.reg_features[FORMAT] = self.instance.register[FORMAT]

        return self.reg_features

    def get_immediate_operand_rule(self) -> dict:
        return self.instance.immediate_operand

    def createRegisterOperand(self, bank: int = 0, register: int = 0) -> str:
        """Create register string by modifying format str"""
        self.reg_format = self.get_register_rule()[FORMAT]
        self.reg_format = self.reg_format.replace('_regFile_', str(bank))
        self.reg_format = self.reg_format.replace('_register_', str(register))

        return self.reg_format

    def create_immediate_operand(self, value: int = 0, type: str = FORMAT_DESCRIPTION.DEC.value) -> str:
        # Make immediate operand
        imm_rule = self.get_immediate_operand_rule()
        imm_format = imm_rule[FORMAT]

        # immediate type setting
        if imm_rule[type] == None:
            imm_type = ''
        else:
            imm_type = imm_rule[type]

        # convert value
        if type == FORMAT_DESCRIPTION.DEC.value:
            imm_value = str(value)
        else:
            imm_value = self.convert_number(value, type)
        imm_format = imm_format.replace('_x_', str(imm_type))
        imm_format = imm_format + imm_value

        return imm_format

    def convert_number(self, value: int = 0, type: str = FORMAT_DESCRIPTION.BIN.value) -> str:
        # value is always dec
        # Convert bin
        if type == FORMAT_DESCRIPTION.BIN.value:
            return_value = '{:b}'.format(value)
            return return_value
        elif type == FORMAT_DESCRIPTION.HEX.value:
            return_value = '{:x}'.format(value)
            return return_value
        else:
            # error
            return ERROR

    def convertImmediateToDecInt(self, immediate: str, type: str = FORMAT_DESCRIPTION.BIN.value) -> int:
        """converts created immediate values into decimal integer

        Args:
            immediate (str): an immediate string to convert to an decimal integer
            type (str, optional): type, which the immediate has. Defaults to FORMAT_DESCRIPTION.BIN.value.

        Returns:
            int: decimal integer of immediate
        """
        # Make immediate operand
        immRule = self.get_immediate_operand_rule()
        immFormat = immRule[FORMAT]

        # immediate type setting
        if immRule[type] == None:
            immType = ''
        else:
            immType = immRule[type]

        # remove extras from value
        immFormat = immFormat.replace('_x_', "")
        immediate = immediate.replace(immFormat, "")
        immediate = immediate.replace(immType, "")

        if type == FORMAT_DESCRIPTION.DEC.value:
            decInteger = int(immediate)
        if type == FORMAT_DESCRIPTION.HEX.value:
            decInteger = int(immediate, 16)
        if type == FORMAT_DESCRIPTION.BIN:
            decInteger = int(immediate, 2)
        return decInteger

    def getDefaultOperandType(self) -> dict:
        '''Make dict of operand types.'''
        opdict = {}
        for operand in OPERANDS:
            opdict[operand.value] = OPERAND_TYPE.REGISTER

        opdict[OPERANDS.RAND_IMMEDIATE.value] = OPERAND_TYPE.IMMEDIATE

        # the ordering is important for the correct replacement strategy in assembly
        opdict[OPERANDS.TEST_ADDRESS.value] = OPERAND_TYPE.TEST_ADDRESS
        opdict[OPERANDS.INIT_ADDRESS.value] = OPERAND_TYPE.INIT_ADDRESS
        opdict[OPERANDS.ADDRESS4.value] = OPERAND_TYPE.ADDRESS4
        opdict[OPERANDS.ADDRESS3.value] = OPERAND_TYPE.ADDRESS3
        opdict[OPERANDS.ADDRESS2.value] = OPERAND_TYPE.ADDRESS2
        opdict[OPERANDS.ADDRESS.value] = OPERAND_TYPE.ADDRESS
        opdict[OPERANDS.BRANCH_INDEX.value] = OPERAND_TYPE.BRANCH_INDEX
        opdict[OPERANDS.RAND_IMMEDIATE1.value] = OPERAND_TYPE.IMMEDIATE
        opdict[OPERANDS.RAND_IMMEDIATE2.value] = OPERAND_TYPE.IMMEDIATE
        return opdict

    def _checkMemoryBlocked(self, address, aligned, factor, enabledFeatures=None):
        blocked = False
        maxBlockedAddresses = aligned * factor
        if enabledFeatures:
            alignmed = int(enabledFeatures[ADDRESS_ALIGNMENT]) if enabledFeatures[ADDRESS_ALIGNMENT] else aligned
            maxBlockedAddresses = maxBlockedAddresses + alignmed + aligned + 4
            print(maxBlockedAddresses)
        for i in range(maxBlockedAddresses):
            if address + i in self.instance.blockedMemoryAddresses:
                return True
        return blocked

    def _hasDCache(self):
        return len(self.instance.dCacheSpec) != 0

    def _hasICache(self):
        return len(self.instance.iCacheSpec) != 0

    def _getAligned(self, enabledFeatures):
        alignment = None
        if enabledFeatures:
            alignment = enabledFeatures[ADDRESS_ALIGNMENT]
        aligned = 1
        if MEMORY_DESCRIPTION.ALIGNED.value in self.instance.memory_description:
            aligned = self.instance.memory_description[MEMORY_DESCRIPTION.ALIGNED.value]
        if not alignment:
            alignment = aligned
        else:
            alignment = int(alignment)

        factor = 1 if alignment == aligned else 3

        return aligned, factor

    def createRandomMemoryAddress(self, enabledFeatures=None, consequitive=False):
        start = 0
        end = DEFAULT_MAX_MEMORY_ADDRESS

        if MEMORY_DESCRIPTION.OFFSET_ADDRESS.value in self.instance.memory_description:
            if self.instance.startAddress == -1:
                raise Exception("Please Set StartAddress. Not doing so may corrupt the testprogram.")
            start = self.instance.startAddress + self.instance.memory_description[
                MEMORY_DESCRIPTION.OFFSET_ADDRESS.value]
        if MEMORY_DESCRIPTION.END_ADDRESS.value in self.instance.memory_description:
            end = self.instance.memory_description[MEMORY_DESCRIPTION.END_ADDRESS.value]

        aligned, factor = self._getAligned(enabledFeatures)

        if len(self.instance.blockedMemoryAddresses) == 0:
            address = randrange(start, end, aligned)
        else:

            if not self._hasDCache():
                blocked = True
                while blocked:
                    address = randrange(start, end, aligned)
                    blocked = self._checkMemoryBlocked(address, aligned, factor, enabledFeatures)
            else:
                prob = random.uniform(0, 1)
                if prob < self.instance.newMemoryBlock:
                    blocked = True
                    while blocked:
                        address = randrange(start, end, aligned)
                        blocked = self._checkMemoryBlocked(address, aligned, factor, enabledFeatures)

                else:
                    # get address of last word
                    lastAddr = self.instance.blockedMemoryAddresses[-1]
                    offset = lastAddr % aligned
                    lastWordAddress = lastAddr - offset
                    address = int(lastWordAddress + self.instance.getNextMemoryAddress(dataCache=True))

                    # check for consequitive addresses
                    consequitiveNewSearch = False
                    checkConsequitiveCondition = consequitive and enabledFeatures
                    if checkConsequitiveCondition:
                        consequitiveNewSearch = (-1 == self.snoopNextAlignedMemory(address,
                                                                                   enabledFeatures))
                    if address > end or consequitiveNewSearch:
                        # new address is larger than data address range, generate a new random start address
                        blocked = True
                        while blocked:
                            address = randrange(start, end, aligned)
                            blocked = self._checkMemoryBlocked(address, aligned, factor, enabledFeatures)
                            if not blocked and checkConsequitiveCondition:
                                blocked = (-1 == self.snoopNextAlignedMemory(address, enabledFeatures))

        # always block full words (block other bytes of the word)
        for i in range(4):
            self.instance.blockedMemoryAddresses.append(address + i)

        return address

    def snoopNextAlignedMemory(self, address, enabledFeatures):
        # chose TEST_ADDRESS in next aligned memory block depending on local alignment (for store halfword and store byte)
        aligned = self.instance.memory_description[
            MEMORY_DESCRIPTION.ALIGNED.value] if MEMORY_DESCRIPTION.ALIGNED.value in self.instance.memory_description else 1
        alignmed = int(enabledFeatures[ADDRESS_ALIGNMENT]) if enabledFeatures[ADDRESS_ALIGNMENT] else aligned
        shift = randrange(0, aligned, alignmed)
        newAddress = address + aligned + shift

        aligned, factor = self._getAligned(enabledFeatures)
        if self._checkMemoryBlocked(newAddress, aligned, factor):
            return -1
        return newAddress

    def getNextAlignedMemoryAddress(self, address, enabledFeatures):

        newAddress = self.snoopNextAlignedMemory(address, enabledFeatures)
        if newAddress == -1:
            raise Exception("2 consequitive Addresses are not avaiable.")

        aligned, factor = self._getAligned(enabledFeatures)
        # block addresses
        # always block full words (block other bytes of the word)
        for i in range(aligned * factor):
            self.instance.blockedMemoryAddresses.append(newAddress + i)

        return newAddress

    def generateRandomOperands(self, enabledFeatures: Dict[str, Union[str, None]], generateFocusRegister: bool = True,
                               FocusRegister: Union[str, None] = None, sequence: bool = False,
                               plainFocusRegister: Union[str, None] = None, newPlainTargetReg: bool = False,
                               blockRandomRegister=False, randImmediateExtension=None) -> Dict[
        str, Union[str, int]]:
        """Creates for each default operand type a random value.

        Args:
            enabledFeatures (Dict[str, Union[str, None]]): enabled features of the instruction.
            generateFocusRegister (bool, optional): If True, generate focus register. Defaults to True.
            FocusRegister (Union[str, None], optional): If not None use as focus and target register. Defaults to None.
            sequence (bool, optional): If plain register should becreated. Defaults to False.
            plainFocusRegister (Union[str, None], optional): If not None and plain True uses as plain focus and target register. Defaults to None.

        Returns:
            Dict[str,Union[str, int]]: Every operand type and its corresponding random value
        """
        operands = self.getDefaultOperandType()
        for key in operands:
            block = False
            if key == OPERANDS.FOCUS_REGISTER.value:
                if generateFocusRegister:
                    block = True
                elif FocusRegister:
                    operands[key] = FocusRegister
                    continue
                else:
                    continue
            elif key == OPERANDS.TARGET_REGISTER.value:
                if FocusRegister:
                    operands[key] = FocusRegister
                    continue
                else:
                    block = True
            elif key == OPERANDS.PLAIN_FOCUS_REGISTER.value:
                if plainFocusRegister:
                    operands[key] = plainFocusRegister
                    continue
                else:
                    operands[key] = None
                    continue
            elif key == OPERANDS.Sequence_TARGET_REGISTER.value:
                if not sequence:
                    operands[key] = None
                    continue
                if plainFocusRegister:
                    operands[key] = plainFocusRegister
                    continue
                else:
                    block = True
            elif IMMEDIATE in enabledFeatures and key == OPERANDS.RAND_VALUE.value and enabledFeatures[IMMEDIATE]:
                if self.instance.immediateRegister:
                    operands[key] = self.createRegisterOperand(self.instance.immediateRegister[0],
                                                               self.instance.immediateRegister[1])
                    continue
            elif key == OPERANDS.INIT_ADDRESS.value:
                address = self.createRandomMemoryAddress(enabledFeatures, consequitive=True)
                operands[key] = address
                operands[OPERANDS.TEST_ADDRESS.value] = self.getNextAlignedMemoryAddress(address, enabledFeatures)

                continue
            elif key == OPERANDS.TEST_ADDRESS.value:
                continue
            elif randImmediateExtension:
                if key == OPERANDS.RAND_IMMEDIATE1.value or key == OPERANDS.RAND_IMMEDIATE2.value:
                    # random Immediates are always long
                    operands[key] = self.generateRandomOperand(operands[key], {IMMEDIATE: randImmediateExtension},
                                                               block)
                    continue
            # no need to create Register conditions
            if not newPlainTargetReg and key == OPERANDS.Sequence_NEW_TARGET_REGISTER.value:
                operands[key] = None
                continue
            if not sequence and key == OPERANDS.Sequence_TEMP.value:
                operands[key] = None
                continue
            # todo: hotfix for sequences. Will limit total register assignment to available hardware register
            # to fix: Stacks should block focus, target and Sequence register before assigning random register.
            # otherwise sequences could overwrite random values.  BlockRAndomRegister is just a hotfix for switching
            # control from this function to a register drawing function in the stack
            if blockRandomRegister:
                block = True
            operands[key] = self.generateRandomOperand(operands[key], enabledFeatures, block)

        if sequence and plainFocusRegister is None:
            operands[OPERANDS.PLAIN_FOCUS_REGISTER.value] = operands[OPERANDS.Sequence_TARGET_REGISTER.value]
        return operands

    def generateRandomOperand(self, type, enabledFeatures, block=False):
        # If type is register do:
        if type == OPERAND_TYPE.REGISTER:
            if len(self.instance._registerStack) > 0:
                if block:
                    useRegister = self.instance._registerStack.pop()
                else:
                    useRegister = self.instance._registerStack[randint(0, len(self.instance._registerStack) - 1)]
                return self.createRegisterOperand(useRegister[0], useRegister[1])
            else:
                raise Exception("ERROR: Not enough register for all instructions")

        # If type is immediate do:
        elif type == OPERAND_TYPE.IMMEDIATE:
            return self.createRandImmediate(enabledFeatures[IMMEDIATE])
        elif type == OPERAND_TYPE.ADDRESS:
            return self.createRandomMemoryAddress()
        elif type == OPERAND_TYPE.ADDRESS2:
            return self.createRandomMemoryAddress()
        elif type == OPERAND_TYPE.ADDRESS3:
            return self.createRandomMemoryAddress()
        elif type == OPERAND_TYPE.ADDRESS4:
            return self.createRandomMemoryAddress()
        elif type == OPERAND_TYPE.BRANCH_INDEX:
            self.instance.branchIndex += 1
            return self.instance.branchIndex

    def blockRegister(self, register):

        n = 3
        pass

    def getOperandAssembly(self, operandString: str, operandAttributes: Dict[str, Union[str, int, None]],
                           overridingTargetRegister: Union[str, None] = None,
                           isRandValueRandomImmediate: bool = False) -> str:
        """Replaces the key words in the operand string of a instruction with the corresponding operand attribute values.

        Args:
            operandString (str): the operands of the instruction as a string
            operandAttributes (Dict[str, Union[str, int, None]]): the key attributes of the operand with the corresponding values
            overridingTargetRegister (Union[str, None], optional): A target register to overwrite the target register. Defaults to None.
            isRandValueRandomImmediate (bool, optional): If the randValueRegister should be override with the immediate value. Defaults to False.

        Returns:
            str: The operands of the instruction with operands replaced with values
        """
        overwriteRandValue = True
        # randomValue is immediate instead of register
        if OPERANDS.RAND_VALUE.value in operandString and OPERANDS.RAND_IMMEDIATE.value in operandString:
            overwriteRandValue = False
            # operandString = operandString.replace(OPERANDS.RAND_VALUE.value, OPERANDS.RAND_IMMEDIATE.value)

        for operand, value in operandAttributes.items():
            if operand == OPERANDS.TARGET_REGISTER.value and overridingTargetRegister:
                value = overridingTargetRegister

            # custom defined Immediates:
            if (
                    isRandValueRandomImmediate and operand == OPERANDS.RAND_VALUE.value) or operand == OPERANDS.RAND_IMMEDIATE.value:
                if operand + IMM_RANGE.START.value in operandString:
                    immRange = operandString[
                               operandString.index(IMM_RANGE.START.value) + 1: operandString.index(IMM_RANGE.END.value)]
                    operand = operand + IMM_RANGE.START.value + immRange + IMM_RANGE.END.value
                    immRange = immRange.split(IMM_RANGE.SPLIT.value)
                    value = self.getRangeImmediate(operandAttributes[OPERANDS.RAND_IMMEDIATE.value], immRange,
                                                   FORMAT_DESCRIPTION.HEX.value)
                else:
                    if OPERANDS.RAND_VALUE.value == operand and overwriteRandValue:
                        # override random value with immediate
                        value = operandAttributes[OPERANDS.RAND_IMMEDIATE.value]
                    else:
                        value = operandAttributes[operand]

            # custom defined Address ranges
            if operand == OPERANDS.ADDRESS.value and operand + IMM_RANGE.START.value in operandString:
                immRange = operandString[
                           operandString.index(IMM_RANGE.START.value) + 1: operandString.index(IMM_RANGE.END.value)]
                operand = operand + IMM_RANGE.START.value + immRange + IMM_RANGE.END.value
                immRange = immRange.split(IMM_RANGE.SPLIT.value)
                value = self.getRangeImmediate(operandAttributes[OPERANDS.ADDRESS.value], immRange,
                                               FORMAT_DESCRIPTION.DEC.value)
            operandString = operandString.replace(operand, str(value))

        return operandString

    def getRangeImmediate(self, immediate: str, immRange: List[str], type: str) -> str:
        """Creates a immediate in the given bit range from the given immediate.

        Args:
            immediate (str): the immediate to take the range
            immRange (List[str]): first value is highest bit, second lowest
            type (str): the immediate type

        Returns:
            str: the new immediate
        """
        if type == FORMAT_DESCRIPTION.DEC.value:
            decImm = int(immediate)
        else:
            decImm = self.convertImmediateToDecInt(immediate, type)
        binImm = str('{0:0' + str(int(immRange[0]) + 1) + 'b}').format(
            decImm)  # binary value should always have enough bits
        minRange = len(binImm) - int(immRange[0]) - 1
        maxRange = (len(binImm) - int(immRange[1]))
        binImm = binImm[minRange:maxRange]
        decImm = int(binImm, 2)
        return self.create_immediate_operand(decImm, type)

    def generateComparisonCode(self, instr_list: list, focusInstruction, targetInstruction, branchIndex=-1) -> str:
        comparison_code = ''
        for instr in instr_list:
            # get FocusReg of PlainFocusReg
            focusReg = focusInstruction.getFocusOperand()
            targetReg = targetInstruction.getTargetOperand()
            if branchIndex != -1:
                targetReg = targetInstruction.getSequenceTargetOperand()
                focusReg = focusInstruction.getTargetOperand()
            instr = instr.replace(OPERANDS.FOCUS_REGISTER.value, focusReg)
            instr = instr.replace(OPERANDS.TARGET_REGISTER.value, targetReg)
            comparison_code += str(instr)
            comparison_code += '\n'
        if branchIndex != -1:
            compareComment = "Comparison Code " + str(branchIndex) + "\n"
        else:
            compareComment = "Comparison Code\n"
        return '\n' + self.get_assembler_comment() + compareComment + comparison_code

    def generateGlobalPreSequenceCode(self, instr_list: list, Instruction) -> str:
        globalPrePlainCode = ''
        for instr in instr_list:
            # get FocusReg of PlainFocusReg
            focusReg = Instruction.getFocusOperand()
            plainFocusReg = Instruction.getPlainFocusOperand()

            instr = instr.replace(OPERANDS.PLAIN_FOCUS_REGISTER.value, plainFocusReg)
            instr = instr.replace(OPERANDS.FOCUS_REGISTER.value, focusReg)
            globalPrePlainCode += str(instr)
            globalPrePlainCode += '\n'
        return '\n' + self.get_assembler_comment() + "global pre sequence code (TargetRegister = Focusregister for load as 1. sequence instruction)\n" + globalPrePlainCode

    def createUseRegister(self, maxRegFile, maxRegSize):
        return [randint(0, maxRegFile), randint(0, maxRegSize)]

    def createRandImmediate(self, immediateName: str) -> str:
        """creates a random immediate with the processor definitions of the given immediate name.

        Args:
            immediateName (str): name of the immediate type. If default, the immediate default type is used

        Returns:
            str: the created immediate operand 
        """
        if not immediateName:
            return

        for attribute, assembly in self.instance.immediate.items():
            if attribute == immediateName:
                if attribute == DEFAULT:
                    immType = self.getImmediateDefault()
                else:
                    immType = attribute
        # FIXME: immediate smaller than 0/min and max from processor description/ if signed/unsigned - don't set absolute value, but bit-length
        maxValue = int(self.get_immediate_operand_rule()[immType])
        randValue = randint(0, maxValue)
        immBasis = FORMAT_DESCRIPTION.HEX.value
        immOperand = self.create_immediate_operand(randValue, immBasis)
        return immOperand

    def convertInt2Assembly(self, immediate):
        immBasis = FORMAT_DESCRIPTION.HEX.value
        immOperand = self.create_immediate_operand(immediate, immBasis)
        return immOperand

    def append_instr_feature(self, inst):
        attr_dict = {}
        for feature in INSTRUCTION_FEATURE_LIST:
            if feature in inst:
                attr_dict[feature] = inst[feature].split(DELIMITER_FEATURE) if inst[feature] is not None else [None]
            else:
                attr_dict[feature] = [None]

        for feature in INSTRUCTION_SPECIAL_FEATURE:
            if feature in inst:
                attr_dict[feature] = inst[feature].split(DELIMITER_FEATURE) if inst[feature] is not None else [None]
            else:
                attr_dict[feature] = [None]

        for attr_list in attr_dict.values():
            for ind, value in enumerate(attr_list):
                if value == '':
                    attr_list[ind] = None

        feature = {}
        # convert value to Assembly
        for key in attr_dict:
            feature[key] = []
            for value in attr_dict[key]:
                if value == 'None' or value is None:
                    feature[key].append(None)
                else:
                    feature[key].append(self.instance.proc_infos[key][value])
        return feature

    def getRandomIssueSlot(self):
        return randint(0, int(self.instance.issue_slots[MAX_SIZE]));

    def getIgnoreRegister(self) -> List[List[int]]:
        """returns the list of registers to be ignored of the processor

        Returns:
            List[List[int]]: List of registers as lists with registerfile and register as int
        """
        return self.instance._ignoreRegister

    def getRegisterStack(self) -> List[List[int]]:
        """returns the list of registers which are not used yet

        Returns:
            List[List[int]]: List of registers as lists with registerfile and register as int
        """
        return self.instance._registerStack

    def getSIMD(self):
        return self.instance.proc_infos[SIMD]

    def resetBranchIndex(self):
        self.instance.branchIndex = -1

    def resetRegisterStack(self):
        self.instance.createRegisterStack()

    def reset(self):
        self.instance.createRegisterStack()
        self.resetBranchIndex()
        self.instance.setMemoryDescription()
        self.instance.blockedMemoryAddresses = []
        self.instance.startAddress = -1

    def setStartAddress(self, startAddress):
        """

        :param startAddress: Sets the start Address for the address Generation.
        :return: Commented Code describing the startAddress. Can be added to Assembly files for debuggin purposes.
        """
        ''' '''
        if MEMORY_DESCRIPTION.IMEM_OVERLAP.value in self.instance.memory_description:
            addressAlignment = self.instance.memory_description[ADDRESS_ALIGNMENT]
            self.instance.startAddress = startAddress * addressAlignment
            return self.get_assembler_comment() + " Start Address Set to " + str(self.instance.startAddress)
        else:
            self.instance.startAddress = self.instance.memory_description[MEMORY_DESCRIPTION.START_ADDRESS.value]
            return self.get_assembler_comment() + " Default Start ADDRESS " + str(self.instance.startAddress)

    def calculateStartAddress(self, testInstructionList):
        instructionCount = 0
        for testInstruction in testInstructionList:
            counter = testInstruction.calculateEnabledInstructions()
            instructionCount += counter

        return Processor().setStartAddress(instructionCount)

    def getProcessorFeatureAssembly(self, feature, value):

        assembly = self.instance.proc_infos[feature][value]
        if not assembly:
            return value
        else:
            return assembly

    # def getAssemlby2Feature(self, assembly):
    #
    #     if assembly:
    #         for instrFeature in INSTRUCTION_SPECIAL_FEATURE:
    #             if instrFeature not in self.instance.proc_infos:
    #                 return None
    #             else:
    #                 for key, value in self.instance.proc_infos[instrFeature].items():
    #                     if value:
    #                         if assembly in value:
    #                             return key
    #
    #         for instrFeature in INSTRUCTION_FEATURE_LIST:
    #             if instrFeature in self.instance.proc_infos:
    #                 for key, value in self.instance.proc_infos[instrFeature].items():
    #                     if assembly in key:
    #                         return value
    #     else:
    #         return None

    def getImmediateDefault(self) -> str:
        """returns the default type for immediate from pocessor descrption

        Returns:
            str: default type for immediate
        """
        return self.instance.immediate[DEFAULT]

    def get_assembler_comment(self):
        return self.instance.proc_infos['comment']

    def get_assembler_ending(self):
        return self.instance.proc_infos['assembler-ending']

    def getMaxBranchDistance(self):
        return self.instance.maxBranchDistance

    def getIMemJumpInstructions(self):
        return self.instance.getIMemJumpInstructions()

    def hasIMemJump(self):
        return bool(self.instance.iCacheSpec)
