# Copyright (c) 2022 Chair for Chip Design for Embedded Computing,
#                    Technische Universitaet Braunschweig, Germany
#                    www.tu-braunschweig.de/en/eis
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
from Constants import *
from util.Processor import Processor


class Operand:
    def __init__(self, bank: int = 0, register: int = 0, immediate: int = None, type: str = 'dec'):
        self.setValue(bank, register, immediate, type)
        self.processor = Processor()

    def string(self):
        if self._type == OPERAND_TYPE.Immediate:
            return '#' + str(self._immediate)
        elif self._type == OPERAND_TYPE.Register:
            reg_format = self.processor.get_register_rule()[FORMAT]
            reg_format = reg_format.replace('_regFile_', str(self._bank))
            reg_format = reg_format.replace('_register_', str(self._register))

            return reg_format

    def setValue(self, bank:int, register:int, immediate:int, type: str):
        if immediate is not None:
            self._type = OPERAND_TYPE.Immediate
            if type == 'dec':
                self._immediate = immediate
            elif type == 'bin':
                self._immediate = bin(immediate)
            elif type == 'hex':
                self._immediate = hex(immediate)

        else:
            self._type = OPERAND_TYPE.Register
            self._bank = bank
            self._register = register