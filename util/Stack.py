# Copyright (c) 2022 Chair for Chip Design for Embedded Computing,
#                    Technische Universitaet Braunschweig, Germany
#                    www.tu-braunschweig.de/en/eis
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT

import copy  # for deepcopy
import itertools
import pickle
import random
from typing import Dict, List

from Constants import *
import Constants
from util.DataBank import DataBank
from util.Processor import Processor
from util.RandomOptions import RandomOptions
from util.TestInstruction import TestInstruction


class Stack:

    def __init__(self, architecture, icacheMissChance, enabled_extensions):
        self.processor = Processor(architecture)
        self._TestInstructions = DataBank(
            architecture, enabled_extensions).getTestInstructions()  # List of Instruction combos (TestInstruction)
        self._instructionsList = []  # List of Testinstr to run (randomized from _TestInstructions)
        self.initRegCounter = 0
        self._BranchLimits: List[int] = []
        self.icacheMissChance = float(icacheMissChance)
        self._restore_operands = None
        self.need_random_block_memory = DataBank().need_random_block_register()

    def generateInstructionsList(self, level: int, singleInstruction="", max_instructions=-1):
        self._instructionsList = []
        if singleInstruction != "":
            for testInstruction in self._TestInstructions:
                if testInstruction.getInstruction().upper() == singleInstruction.upper():
                    self._instructionsList.append(copy.deepcopy(testInstruction))
                    return
        for i in range(level):
            # deep copy elements, because in the instructionlist they are changed.
            # This should not affect all occurences inside the instructionslist
            self._instructionsList.extend(copy.deepcopy(self._TestInstructions))
        random.shuffle(self._instructionsList)
        
        if max_instructions > 0:
            self._instructionsList = self._instructionsList[:max_instructions]
        
        if self._instructionsList[0].getInstruction() == NOP_INSTR:
            nopInstr = self._instructionsList[0]
            for index in range(len(self._instructionsList)):
                testInstr = self._instructionsList[index]
                if testInstr.getInstruction() != NOP_INSTR:
                    break;
            noNopInstr = self._instructionsList[index]
            self._instructionsList[0] = noNopInstr
            self._instructionsList[index] = nopInstr

    def _checkImemCacheMissOpportunities(self, instructionList, outsideSequenceUsage=False):
        prob = random.uniform(0, 1)
        if prob < self.icacheMissChance:
            # get IcacheJumpInstructions

            # get indices
            lastIndex = 0
            counter = 0
            for endInstr in self._BranchLimits:
                for startInst in self._BranchStart:
                    if startInst > lastIndex:
                        index = startInst - 1 + counter
                        if index > 0:
                            lastIndex = len(instructionList)
                            icacheMissInstruction = DataBank().getICacheMissTestInstruction()
                            icacheMissInstruction.set_random_features(0.0, 0.0)
                            icacheMissInstruction.isOutsideSequenceUsed(outsideSequenceUsage)
                            instructionList.insert(index, icacheMissInstruction)
                            counter += 1
                        break
            self._sanitizeBranches(instructionList)

    def generateSequenceInstructionsList(self, sequenceLength=4):
        instructions = {}
        # first instruction cannot be nop
        noNopInstructions = {}
        for testInstruction in self._TestInstructions:
            if testInstruction.hasValidSequenceInstruction():
                type = testInstruction.getType()
                if type not in instructions:
                    instructions[type] = []
                    noNopInstructions[type] = []
                instructions[type].append(copy.deepcopy(testInstruction))
                # first instruction cannot be nop
                if testInstruction.getInstruction() != NOP_INSTR:
                    noNopInstructions[type].append(copy.deepcopy(testInstruction))

        diffInstrTypes = instructions.keys()
        instructionsList = []
        results = itertools.product(list(diffInstrTypes), repeat=sequenceLength)
        for combination in results:
            temp = []
            listKeys = []
            for index in range(len(combination)):
                key = combination[index]
                listKeys.append(key)
                instrList = instructions
                if index == 0:
                    instrList = noNopInstructions
                temp.append(copy.deepcopy(random.choice(instrList[key])))

            instructionsList.append(temp)
        print(len(instructionsList))
        return instructionsList

    def _getSequenceKey(self, instructionTypes, stallTypes, forwardingStallProb):
        key = list(instructionTypes.keys())[0]
        prob = random.uniform(0, 1)
        if prob <= forwardingStallProb and len(stallTypes) > 0:
            key = random.choice(stallTypes)
        return key

    def generateSingleSequence(self, length, forwardingStallProb=0.0):
        """
        :return: Returns a list of R-type instructions to interrupt a Sequence
        """
        instructions = {}
        # first instruction cannot be nop
        noNopInstructions = {}
        # stall Instructions
        stallTypes = []
        for testInstruction in self._TestInstructions:
            if testInstruction.hasValidSequenceInstruction():
                type = testInstruction.getType()
                if type not in instructions:
                    instructions[type] = []
                    noNopInstructions[type] = []
                if MULTI_CYCLE_INSTRUCTION_TYPE in type:
                    stallTypes.append(type)

                instructions[type].append(copy.deepcopy(testInstruction))
                # first instruction cannot be nop
                if testInstruction.getInstruction() != NOP_INSTR:
                    noNopInstructions[type].append(copy.deepcopy(testInstruction))

        temp = []
        key = self._getSequenceKey(noNopInstructions, stallTypes, forwardingStallProb)
        temp.append(copy.deepcopy(random.choice(noNopInstructions[key])))
        for i in range(length - 1):
            key = self._getSequenceKey(noNopInstructions, stallTypes, forwardingStallProb)
            temp.append(copy.deepcopy(random.choice(instructions[key])))
        return temp

    def _chainInstructions(self, testInstructions: List[TestInstruction], switchProbability=0.0, sequence=False,
                           blockRandomRegister=False):
        """
        Set Register chain of Focus and Target register.
        :param testInstructions: List of instruction to chain together
        :param switchProbability: 0 to 1.0. probability of an instruction switching the position of Focus and random operand.
        """
        focus_register = None
        sequenceFocusRegister = None
        i = 0
        for testInstruction in testInstructions:

            testInstruction.generateRandomOperands(focusRegister=focus_register, sequence=sequence,
                                                   sequenceFocusRegister=sequenceFocusRegister,
                                                   blockRandomRegister=blockRandomRegister)
            # should only be necessary on first testInstruciton, since Fosuc_register doesnt change
            focus_register = testInstruction.getTargetOperand()
            if testInstruction.hasNewSequenceTargetReg():
                sequenceFocusRegister = testInstruction.getNewSequenceTargetOperand()
            else:
                sequenceFocusRegister = testInstruction.getSequenceTargetOperand()
            i += 1

        for testInstruction in testInstructions:
            testInstruction.setTargetRegister(focus_register)

    def randomizeInstructionListFeatures(self, immediateProbability=0.0, switchProbability=0.0):
        for testInstruction in self._instructionsList:
            testInstruction.set_random_features(immediateProbability, switchProbability)
            # todo: testing Kavuaka Conditional Execution
            # testInstruction.setEnableFeature(CONDITIONAL, "CRS")

    def _generateModCode(self, instructions: List[TestInstruction], sequenceDebugInfo=-1, interleaving=False):
        code = ""
        interleaving_instr = DataBank().get_pre_random_to_memory() if interleaving else []
        for i, instr in enumerate(instructions):
            code += instr.generateModificationCode(i, interleaving_instr)
            code += Processor().get_assembler_comment() +"new MOD starting\n"
        return code

    def _generateReverseCode(self, instructions: List[TestInstruction], sequenceDebugInfo=-1, interleaving=False):
        code = ""
        interleaving_instr = DataBank().get_post_random_to_memory() if interleaving else []
        counter = len(instructions) - 1
        for instr in reversed(instructions):
            code += instr.generateReversiCode(counter, interleaving_instr)
            counter -=1
        return code

    def generateCodeFull(self, interleaving=False):
        sequences: List[TestInstruction] = [self._instructionsList]
        if len(self._BranchLimits) > 0:
            sequences = []
            previousIndex = 0
            for index in self._BranchLimits:
                temp = self._instructionsList[previousIndex:index]
                sequences.append(temp)
                previousIndex = index
            sequences.append(self._instructionsList[previousIndex:-1])

        code = ''
        for i in range(len(sequences)):
            sequence: List[TestInstruction] = sequences[i]
            try:
                code += "\n" + Processor().get_assembler_comment() + "Starting Sequence " + str(i) + "\n"
                # generate Code
                code += self._generateModCode(sequence, i, interleaving)
                # generate Reversi
                code += self._generateReverseCode(sequence, i, interleaving)
                code += "\n" + Processor().get_assembler_comment() + "Ending Sequence " + str(i) + "\n"
            except Exception as e:
                # dump sequence 
                with open("interleaving_branch_bug", "wb") as fd:
                    pickle.dump(sequence, fd)
                raise Exception(e)

        # generate comparison code
        code += self.generateComparisonCode(self._instructionsList)

        return code

    def getTotalInstructions(self, instructionList):
        instructionCount = 0
        for instr in instructionList:
            instructionCount += instr.getInstructionCount()
        return instructionCount

    def generateComparisonCode(self, instructionList: List[TestInstruction]):
        """Generates the comparison code by reading it from the xml."""
        focusInstruction = instructionList[0]
        targetInstruction = instructionList[-1]
        comparisionCode = DataBank().getComparisonCode()

        return self.processor.generateComparisonCode(comparisionCode, focusInstruction, targetInstruction)

    def generate_comparison_code(self, focusInstructionNumber, targetInstructionNumber) -> str:
        """Generates the comparison code by reading it from the xml."""
        focusInstruction = self._instructionsList[focusInstructionNumber]
        targetInstruction = self._instructionsList[targetInstructionNumber]
        comparisionCode = DataBank().getComparisonCode()

        return self.processor.generateComparisonCode(comparisionCode, focusInstruction, targetInstruction)

    def _createInterleavingInstructions(self, level: int = 1, immediateProbability=0.0, switchProbability=0.0,
                                        specialImmediates=0.0, max_instructions=-1):
        self.generateInstructionsList(level, max_instructions=max_instructions)
        self._setRandomFeatures(self._instructionsList, immediateProbability, switchProbability)
        self._sanitizeBranches(self._instructionsList)
        if Processor()._hasICache():
            self._checkImemCacheMissOpportunities(self._instructionsList, outsideSequenceUsage=True)

        code = ""
        code += Processor().calculateStartAddress(self._instructionsList)
        self._chainInstructions(self._instructionsList, switchProbability, blockRandomRegister=self.need_random_block_memory)

        instructionCount = 0
        c, i = self._generateSpecialImmediateCode(self._instructionsList, specialImmediates)
        code += c
        instructionCount += i

        code += self.generateCodeFull(interleaving=True)
        instructionCount += self.getTotalInstructions(self._instructionsList)

        testInstructions = len(self._instructionsList)
        # reset instr list
        calculatedInstructions = Processor().instance.startAddress
        self.reset()
        return code, testInstructions, instructionCount

    def _setRandomFeatures(self, testInstructions: List[TestInstruction], immediateProbability, switchProbability):
        for instr in testInstructions:
            instr.set_random_features(immediateProbability, switchProbability)

    def _generateCodeSequence(self, instructionList: List[TestInstruction], forwarding, immediateProbability=0.0,
                              switchProbability=0.0, specialImmediates=0.0, forwardingStallProb=0.0):
        # only create one big intermediate chain
        sequence = []
        if forwarding > 0:
            sequence = self.generateSingleSequence(len(instructionList) * forwarding,
                                                   forwardingStallProb=forwardingStallProb)

        code = ""

        # set random features
        self._setRandomFeatures(instructionList, immediateProbability, switchProbability)
        if forwarding > 0:
            self._setRandomFeatures(sequence, immediateProbability, switchProbability)

        # calculate start Address of dmem
        code += Processor().setStartAddress(self._getSequenceInstructionCount(instructionList, sequence))
        # chain instructions
        self._chainInstructions(instructionList, switchProbability=switchProbability, sequence=True,
                                blockRandomRegister=True)
        if forwarding > 0:
            self._chainInstructions(sequence, switchProbability, sequence=True)

        instructionCount = 0
        c, i = self._generateSpecialImmediateCode(instructionList, specialImmediates)
        code += c
        instructionCount += i

        code += self._generateModCode(instructionList)
        if sequence:
            code += "\n\n" + Processor().get_assembler_comment() + " Forward Chain  ###################\n"
            code += self._generateModCode(sequence)

        # generate global pre Sequence Code
        code += "\n"
        code += Processor().generateGlobalPreSequenceCode(DataBank().getGlobalPreSequenceCode(), instructionList[0])

        # generate pre Sequence Code
        code += "\n" + Processor().get_assembler_comment() + "pre sequence code" + "\n"
        for instr in instructionList:
            code += instr.generatePreSequenceCode()
        code += "\n"

        # generate Sequence Code
        code += Processor().get_assembler_comment() + "sequence code" + "\n"
        interleavingCounter = 0
        for i in range(len(instructionList)):

            code += instructionList[i].generateSequenceCode()
            for filler in range(forwarding):
                code += sequence[interleavingCounter].generateSequenceCode()
                interleavingCounter += 1
        code += "\n"

        # generate post Sequence Code
        code += "\n" + "\n" + Processor().get_assembler_comment() + "post sequence code" + "\n"
        for instr in instructionList:
            code += instr.generatePostSequenceCode()
        code += "\n"

        code += Processor().generateComparisonCode(DataBank().getComparisonCode(), instructionList[0],
                                                   instructionList[-1], 1)

        # generate Reversi
        code += self._generateReverseCode(instructionList)
        # generate comparison code
        code += self.generateComparisonCode(instructionList)

        totalInstructions = len(instructionList)

        # add instructions from tests
        for instr in instructionList:
            instructionCount += instr.getInstructionCount()

        if forwarding > 0:
            totalInstructions += forwarding * len(sequence)
            for instr in sequence:
                instructionCount += instr.getInstructionCount()

        self.reset()

        return code, totalInstructions, instructionCount

    def _getSequenceInstructionCount(self, instructionList, sequenceInstructions):
        """
        Error in the calculation of Sequences. Is missing _generateSpecialImmediateCode, but is minor (<2) per missed instance.
        If your specialImmediateCode is large and occurs often, please update the instruction count for the start address of the data.
        :param instructionList:
        :param sequenceInstructions:
        :return:
        """
        instrCount = 0
        # get normal testinstruction
        for testInstruction in instructionList:
            instrCount += testInstruction.calculateEnabledInstructions(sequence=True)

        # get normal testinstruction
        for testInstruction in sequenceInstructions:
            instrCount += testInstruction.calculateEnabledInstructions(standardReversi=False, sequenceHole=True)

        return instrCount

    def _generateSpecialImmediateCode(self, instructionList, specialImmediates):
        code = ""
        instrCount = 0
        randValue = random.uniform(0, 1)
        if randValue < specialImmediates:
            for instr in instructionList:
                if instr.hasSpecialImmediates():
                    c, i = DataBank().getFixedImmediateCode(instr.getOperands(), Processor().convertInt2Assembly(
                        random.choice(instr.getSpecialImmediates())))
                    code += c
                    instrCount += i
        return code, instrCount

    def _sanitizeBranches(self, instructionList):
        self._BranchLimits: List[int] = []
        self._BranchStart: List[int] = []
        # already need correct features enabled.
        maxBranchDist = Processor().getMaxBranchDistance()
        if maxBranchDist > 0:
            instructionCount = 0
            limitBranchSeqeunce = False
            for i in range(len(instructionList)):
                instr = instructionList[i]
                if instr.hasBranchAcrossTestCase() and not instr.isICacheJump():
                    limitBranchSeqeunce = True
                    self._BranchStart.append(i)
                if limitBranchSeqeunce:
                    instructionCount += instr.calculateEnabledInstructions()
                if instructionCount > maxBranchDist:
                    self._BranchLimits.append(i - 1)
                    limitBranchSeqeunce = instr.hasBranchAcrossTestCase()
                    instructionCount = instr.calculateEnabledInstructions()

    def reset(self):
        self._instructionsList = []
        self._BranchLimits = []

    def createInterleavingInstructions(self, random_ops, level: int = 1, immediateProbability=0.0, switchProbability=0.0,
                                       specialImmediates=0.0, max_instructions=-1):
        if random_ops.has_init_reg_file():
            code = DataBank().assemblyRandomizeRegisterFile(randomize_immediate=random_ops.has_init_immidiate())
        else:
            code = ""
        
        testCode, testInstructions, instructionCount = self._createInterleavingInstructions(level, immediateProbability,
                                                                                            switchProbability,
                                                                                            specialImmediates, max_instructions=max_instructions)
        code += testCode
        # reset processor for next independent execution
        self.reset()
        Processor().reset()
        return code, testInstructions, instructionCount

    def createSequenceInstructions(self, instructionList, random_ops, immediateProbability=0.0, switchProbability=0.0, forwarding=0,
                                   specialImmediates=0.0, forwardingStallProb=0.0):
        
        if random_ops.has_init_reg_file():
            code = DataBank().assemblyRandomizeRegisterFile(random_ops.has_init_immidiate())
        else:
            code = ""
        
        testCode, testInstructions, instructionCount = self._generateCodeSequence(instructionList, forwarding,
                                                                                  immediateProbability,
                                                                                  switchProbability, specialImmediates,
                                                                                  forwardingStallProb=forwardingStallProb)
        code += testCode
        # reset processor for next independent execution
        self.reset()
        Processor().reset()
        return code, testInstructions, instructionCount

    def createSingleInstructions(self, level: int = 1, immediateProbability: float = 0.0,
                                 switchProbability: float = 0.0, randomize_immediate=True):
        
        code = DataBank().assemblyRandomizeRegisterFile(randomize_immediate)
        self.generateInstructionsList(level)
        self.randomizeInstructionListFeatures(immediateProbability, switchProbability)
        for index in range(len(self._instructionsList)):
            testInstruction: TestInstruction = self._instructionsList[index]
            testInstruction.generateRandomOperands(None)
            code += testInstruction.generateModificationCode()
            code += testInstruction.generateReversiCode()
            code += self.generate_comparison_code(index, index)
            Processor().resetRegisterStack()
        totalInstructions = self.getTotalInstructions()
        testInstruction = len(self._instructionsList)
        self.reset()
        return code, testInstruction, totalInstructions

    def createSingleInstructionTest(self, random_ops, immediateProbability=0.0, switchProbability=0.0, singleInstruction=""):
        result = []
        self.generateInstructionsList(1, singleInstruction)
        self.randomizeInstructionListFeatures(immediateProbability, switchProbability)
        totalInstructions = 0
        for index in range(len(self._instructionsList)):
            testInstruction: TestInstruction = self._instructionsList[index]
            
            assembly = self._generate_single_test_assembly(testInstruction, index, random_ops=random_ops)
         
            result.append([testInstruction.getInstruction(), assembly])

        return result, len(self._instructionsList), totalInstructions
        

    def create_basic_instruction_test(self, random_ops: RandomOptions, singleInstruction: str = "") -> Dict[str, str]:
        """ Dont test special codes. Creates for each possible feature combination for each instruction (or specific ones) its own assembly test code. This method is for debugging purposes only.

        Args:
            singleInstruction (str, optional): If only specific instructions should be tested, the name of the instruction . Defaults to "".

        Returns:
            Dict[str, str]: The identifying name of each combination with its assembly code.
        """
        result = {}
        self.generateInstructionsList(1, singleInstruction)
        testInstructionCount = 0
        totalInstructions = 0
        # going through every instruction in xml list
        for index in range(len(self._instructionsList)):
            if True:
                # if self._instructionsList[index].getInstruction() != NOP_INSTR:
                # v equals features of currently choosen instruction
                features = Processor().getAvailableInstructionFeaturesNames(
                    self._instructionsList[index].getInstruction())
                testInstruction: TestInstruction = self._instructionsList[index]
                for immidiateAttr in features[IMMEDIATE]:
                    testInstruction.setEnableFeatureName(IMMEDIATE, immidiateAttr)
                    for alignedVal in features[ADDRESS_ALIGNMENT]:
                        testInstruction.setEnableFeature(ADDRESS_ALIGNMENT, alignedVal)
                        for conditionAttr in features[CONDITIONAL]:
                            testInstruction.setEnableFeatureName(CONDITIONAL, conditionAttr)
                            for flagCondSettings in Processor().getFeatureAttributes(CONDITIONAL_READ) or [None]:
                                if conditionAttr == CONDITIONAL_READ:
                                    testInstruction.setEnableFeature(CONDITIONAL_READ, flagCondSettings)
                                for saturationAttr in features[SATURATION]:
                                    testInstruction.setEnableFeatureName(SATURATION, saturationAttr)
                                    for signageAttr in features[SIGNAGE]:
                                        testInstruction.setEnableFeatureName(SIGNAGE, signageAttr)
                                        for simdAttr in features[SIMD]:
                                            testInstruction.setEnableFeatureName(SIMD, simdAttr)

                                            # distinct enabled features naming string as key for code in dict
                                            # idea: name equal to instruction name
                                            enabledFeaturesString = ""
                                            enabledFeaturesString += "_" + "I" + "-" + immidiateAttr if immidiateAttr else ""
                                            enabledFeaturesString += "_" + "Addr" + "-" + alignedVal if alignedVal else ""
                                            enabledFeaturesString += "_" + "Cond" + "-" + conditionAttr if conditionAttr else ""
                                            enabledFeaturesString += "-" + flagCondSettings if flagCondSettings and conditionAttr == CONDITIONAL_READ else ""
                                            enabledFeaturesString += "_" + "Sat" + "-" + saturationAttr if saturationAttr else ""
                                            enabledFeaturesString += "_" + "Sig" + "-" + signageAttr if signageAttr else ""
                                            enabledFeaturesString += "_" + SIMD + "-" + simdAttr if simdAttr else ""

                                            key = testInstruction.getInstruction() + enabledFeaturesString
                                            if key not in result:
                                                assembly = self._generate_single_test_assembly(testInstruction, index, random_ops=random_ops)
                                                
                                                result[testInstruction.getInstruction() + enabledFeaturesString] = assembly
                                                testInstructionCount += 1
                                                totalInstructions += testInstruction.getInstructionCount()
                                            
                                            Processor().reset()

        return result, testInstructionCount, totalInstructions
    
    def _set_restore_operands(self, testInstructionOperands, enabledFeatures):
        operands = Processor().generateRandomOperands(enabledFeatures, generateFocusRegister=False,
                                                      randImmediateExtension=DataBank().instance.randomImmediateType)
        operands[OPERANDS.FOCUS_REGISTER.value] = testInstructionOperands[OPERANDS.FOCUS_REGISTER.value]
        operands[OPERANDS.TARGET_REGISTER.value] = testInstructionOperands[OPERANDS.TARGET_REGISTER.value]
        operands[OPERANDS.RAND_VALUE.value] = testInstructionOperands[OPERANDS.RAND_VALUE.value]
        # if loading from memory, set the memory address
        # in pre code, there can be ADDRESS that will use the start address and then increment it
        operands[OPERANDS.ADDRESS.value] = Processor().get_processor_state_random_start_address()
        self._restore_operands = operands
        
    def _get_restore_operands(self):
        return self._restore_operands
        

    def _generate_single_test_assembly(self,  testInstruction: TestInstruction, index: int, random_ops:RandomOptions):
        # generate code
        if random_ops.has_init_reg_file():
            code = DataBank().assemblyRandomizeRegisterFile(random_ops.has_init_immidiate())
        else:
            code = ""
        
        code += Processor().setStartAddress(
            testInstruction.calculateEnabledInstructions())
        testInstruction.generateRandomOperands()
        code += testInstruction.generateModificationCode()
        
        # randomize processor state
        if random_ops.has_random_processor_state():
            self._set_restore_operands(testInstruction.getOperands(), testInstruction.getEnabledFeatures())
            restore_operands = self._get_restore_operands()
            code += DataBank().randomizeProcessorState(
                restore_operands, random_ops)
            
            # restore focus register after processor state randomization
            # some operations need the focus register in their reversi code, 
            # therefore it has to be restored after the processor state randomization
            code += DataBank().restoreRandomizedFocusRegister(restore_operands)
        
        code += testInstruction.generateReversiCode()
        
        
        
        code += self.generate_comparison_code(index, index)
        return code
        


    def create_complete_instruction_test(self, random_ops:RandomOptions, singleInstruction: str = "") -> Dict[str, str]:
        """Creates for each possible feature combination for each instruction (or specific ones) its own assembly test code. 
        Contains create_basic_instruction_test, additionally adds operand switchsing (i.e. random operand is now in operand 0 instead of only operand 1).
        Needed for forwarding tests of source operand 0.

        Args:
            singleInstruction (str, optional): If only specific instructions should be tested, the name of the instruction . Defaults to "".

        Returns:
            Dict[str, str]: The identifying name of each combination with its assembly code.
        """
        result = {}
        self.generateInstructionsList(1, singleInstruction)
        testInstructionCount = 0
        totalInstructions = 0
        # going through every instruction in xml list
        for index in range(len(self._instructionsList)):
            if self._instructionsList[index].getInstruction() != NOP_INSTR:
                # v equals features of currently choosen instruction
                features = Processor().getAvailableInstructionFeaturesNames(
                    self._instructionsList[index].getInstruction())
                testInstruction: TestInstruction = self._instructionsList[index]
                for immidiateAttr in features[IMMEDIATE]:
                    testInstruction.setEnableFeatureName(IMMEDIATE, immidiateAttr)
                    for alignedVal in features[ADDRESS_ALIGNMENT]:
                        testInstruction.setEnableFeature(ADDRESS_ALIGNMENT, alignedVal)
                        for conditionAttr in features[CONDITIONAL]:
                            testInstruction.setEnableFeatureName(CONDITIONAL, conditionAttr)
                            for flagCondSettings in Processor().getFeatureAttributes(CONDITIONAL_READ) or [None]:
                                if conditionAttr == CONDITIONAL_READ:
                                    testInstruction.setEnableFeature(CONDITIONAL_READ, flagCondSettings)
                                for saturationAttr in features[SATURATION]:
                                    testInstruction.setEnableFeatureName(SATURATION, saturationAttr)
                                    for signageAttr in features[SIGNAGE]:
                                        testInstruction.setEnableFeatureName(SIGNAGE, signageAttr)
                                        for simdAttr in features[SIMD]:
                                            testInstruction.setEnableFeatureName(SIMD, simdAttr)
                                            for switchAttr in features[SWITCH]:
                                                if immidiateAttr:
                                                    switchAttr = None
                                                testInstruction.setEnableFeatureName(SWITCH, switchAttr)
                                                
                                                 # distinct enabled features naming string as key for code in dict
                                                # idea: name equal to instruction name
                                                enabledFeaturesString = ""
                                                enabledFeaturesString += "_" + "I" + "-" + immidiateAttr if immidiateAttr else ""
                                                enabledFeaturesString += "_" + "Addr" + "-" + alignedVal if alignedVal else ""
                                                enabledFeaturesString += "_" + "Cond" + "-" + conditionAttr if conditionAttr else ""
                                                enabledFeaturesString += "-" + flagCondSettings if flagCondSettings and conditionAttr == CONDITIONAL_READ else ""
                                                enabledFeaturesString += "_" + "Sat" + "-" + saturationAttr if saturationAttr else ""
                                                enabledFeaturesString += "_" + "Sig" + "-" + signageAttr if signageAttr else ""
                                                enabledFeaturesString += "_" + SIMD + "-" + simdAttr if simdAttr else ""
                                                enabledFeaturesString += "_" + "sw" + "-" + switchAttr if switchAttr else ""

                                                key = testInstruction.getInstruction() + enabledFeaturesString
                                                if key not in result:
                                                    assembly = self._generate_single_test_assembly(testInstruction, index, random_ops)
                                                    
                                                    result[key] = assembly
                                                    testInstructionCount += 1
                                                    totalInstructions += testInstruction.getInstructionCount()
                                                
                                                Processor().reset()

        return result, testInstructionCount, totalInstructions

    def get_comment(self):
        return self.processor["comment"]
