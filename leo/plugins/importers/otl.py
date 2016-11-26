#@+leo-ver=5-thin
#@+node:ekr.20140723122936.18150: * @file importers/otl.py
'''The @auto importer for vim-outline files.'''
import re
import leo.core.leoGlobals as g
import leo.plugins.importers.linescanner as linescanner
Importer = linescanner.Importer
#@+others
#@+node:ekr.20161124034614.2: ** class Otl_Importer
class Otl_Importer(Importer):
    '''The importer for the otl lanuage.'''

    def __init__(self, importCommands, atAuto):
        '''Otl_Importer.__init__'''
        # Init the base class.
        Importer.__init__(self,
            importCommands,
            atAuto = atAuto,
            language = 'plain',
            state_class = None,
            strict = False,
        )
        
    #@+others
    #@+node:ekr.20161124035243.1: *3* otl_i.v2_gen_lines & helper
    # Must match body pattern first.
    otl_body_pattern = re.compile(r'^: (.*)$')
    otl_pattern      = re.compile(r'^[ ]*(\t*)(.*)$')

    def v2_gen_lines(self, s, parent):
        '''Node generator for otl (vim-outline) mode.'''
        self.inject_lines_ivar(parent)
        # We may as well do this first.  See warning below.
        self.add_line(parent, '@others\n')
        self.parents = [parent]
        for line in g.splitLines(s):
            m = self.otl_body_pattern.match(line)
            if m:
                p = self.parents[-1]
                self.add_line(p, m.group(1))
            else:
                m = self.otl_pattern.match(line)
                if m:
                    # Cut back the stack, then allocate a new node.
                    level = 1 + len(m.group(1))
                    self.parents = self.parents[:level]
                    self.find_parent(
                        level = level,
                        h = m.group(2).strip())
                else:
                    self.error('Bad otl line: %r' % line)
        # This warning *is* correct.
        warning = '\nWarning: this node is ignored when writing this file.\n\n'
        self.add_line(self.root, warning)
    #@+node:ekr.20161124035243.2: *4* otl_i.find_parent
    def find_parent(self, level, h):
        '''
        Return the parent at the indicated level, allocating
        place-holder nodes as necessary.
        '''
        assert level >= 0
        while level >= len(self.parents):
            child = self.v2_create_child_node(
                parent = self.parents[-1],
                body = None,
                headline = h,
            )
            self.parents.append(child)
        return self.parents[level]
    #@+node:ekr.20161125221742.1: *3* otl_i.delete_all_empty_nodes
    def delete_all_empty_nodes(self, parent):
        '''Override the base class so we *dont* delete empty nodes!'''
    #@+node:ekr.20161126074028.1: *3* otl_i.post_pass
    def post_pass(self, parent):
        '''
        Optional Stage 2 of the importer pipeline, consisting of zero or more
        substages. Each substage alters nodes in various ways.
        
        Subclasses may freely override this method, **provided** that all
        substages use the API for setting body text. Changing p.b directly will
        cause asserts to fail later in i.finish().
        '''
        # Do nothing!
    #@-others
#@-others
importer_dict = {
    '@auto': ['@auto-otl', '@auto-vim-outline',],
    'class': Otl_Importer,
    'extensions': ['.otl',],
}
#@-leo
