# Copyright (c) 2022 Chair for Chip Design for Embedded Computing,
#                    Technische Universitaet Braunschweig, Germany
#                    www.tu-braunschweig.de/en/eis
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT

class RandomOptions:
    def __init__(self, args):
        if args.not_randomize and (args.randomize_init_load or args.randomize_init_immediate):
            raise Exception("--not_randomize assumes, that the header performs the randomization. Cannot randomize register-file in the init-randomization and not randomize at the same time. Incompatible options.\n--not_randomize and --randomize_init_load/--randomize_init_immediate")
        if args.randomize_init_load and args.randomize_init_immediate:
            raise Exception("Cannot randomize register-file in the init-randomization with load instructions and immediate values at the same time. Incompatible options.\n--randomize_init_load and --randomize_init_immediate")
        if args.randomize_processor_state_load and args.randomize_processor_state_immediate:
            raise Exception("Cannot randomize register-file in the processor-state-randomization with load instructions and immediate values at the same time. Incompatible options.\n--randomize_processor_state_load and --randomize_processor_state_immediate")
        if args.randomize_init_load and args.randomize_processor_state_immediate:
            raise Exception("Randomization has to be consistent between init-randomization and processor-state-randomization. Incompatible options.\n--randomize_init_load and --randomize_processor_state_immediate")
        if args.randomize_init_immediate and args.randomize_processor_state_load:
            raise Exception("Randomization has to be consistent between init-randomization and processor-state-randomization. Incompatible options.\n--randomize_init_immediate and --randomize_processor_state_load")
        
        # init reg-file randomization
        self.random_init = args.randomize_init_load or args.randomize_init_immediate
        self.random_init_load = args.randomize_init_load
        self.random_init_immediate = args.randomize_init_immediate
        self.not_randomize = args.not_randomize
        
        # processor reg-file randomization
        self.random_processor_state = args.randomize_processor_state_load or args.randomize_processor_state_immediate or args.randomize_processor_state
        self.random_processor_state_load = args.randomize_processor_state_load
        self.random_processor_state_immediate = args.randomize_processor_state_immediate
        
        
        
    
    def has_init_reg_file(self):
        return self.random_init
    
    def has_random_init_reg_file(self):
        return not self.not_randomize
    
    def has_init_immidiate(self):
        return self.random_init_immediate
    
    
    def has_random_processor_state(self):
        return self.random_processor_state
    
    def has_random_processor_method(self):
        return self.random_processor_state_load or self.random_processor_state_immediate
    
    def has_random_processor_state_immediate(self):
        return self.random_processor_state_immediate
    