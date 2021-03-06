# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20170419092835.1: * @file cursesGui2.py
#@@first
'''A prototype text gui using the python curses library.'''
#@+<< cursesGui imports >>
#@+node:ekr.20170419172102.1: ** << cursesGui imports >>
import copy
import logging
import logging.handlers
# import re
import sys
# import time
try:
    from tkinter import Tk # Python 3
except ImportError:
    from Tkinter import Tk # Python 2
# import weakref
import leo.core.leoGlobals as g
import leo.core.leoFrame as leoFrame
import leo.core.leoGui as leoGui
import leo.core.leoMenu as leoMenu
import leo.core.leoNodes as leoNodes
# import leo.core.leoPlugins as leoPlugins
try:
    import curses
except ImportError:
    curses = None

npyscreen = g.importExtension(
    'npyscreen',
    pluginName=None,
    required=True,
    verbose=False,
)

if npyscreen:
    import npyscreen.utilNotify as utilNotify
    assert utilNotify
#@-<< cursesGui imports >>
# pylint: disable=arguments-differ,logging-not-lazy
native = True
    # True: use native Leo data structures, replacing the
    # the values property by a singleton LeoValues object.
#@+<< forward reference classes >>
#@+node:ekr.20170511053555.1: **  << forward reference classes >>
# These classes aren't necessarily base classes, but
# they must be defined before classes that refer to them.
#@+others
#@+node:ekr.20170507184329.1: *3* class LeoTreeData (npyscreen.TreeData)
class LeoTreeData(npyscreen.TreeData):
    '''A TreeData class that has a len and new_first_child methods.'''
    #@+<< about LeoTreeData ivars >>
    #@+node:ekr.20170516143500.1: *4* << about LeoTreeData ivars >>
    # EKR: TreeData.__init__ sets the following ivars for keyword args.
        # self._parent # None or weakref.proxy(parent)
        # self.content.
        # self.selectable = selectable
        # self.selected = selected
        # self.highlight = highlight
        # self.expanded = expanded
        # self._children = []
        # self.ignore_root = ignore_root
        # self.sort = False
        # self.sort_function = sort_function
        # self.sort_function_wrapper = True
    #@-<< about LeoTreeData ivars >>

    def __len__(self):
        if native:
            p = self.content
            assert p and isinstance(p, leoNodes.Position), repr(p)
            content = p.h
        else:
            content = self.content
        return len(content)
        
    def __repr__ (self):
        if native:
            p = self.content
            assert p and isinstance(p, leoNodes.Position), repr(p)
            return '<LeoTreeData: %s, %s>' % (id(p), p.h)
        else:
            return '<LeoTreeData: %r>' % self.content
    __str__ = __repr__
    
    #@+others
    #@+node:ekr.20170516153211.1: *4* LeoTreeData.__getitem__
    def __getitem__(self, n):
        '''Return the n'th item in this tree.'''
        aList = self.get_tree_as_list()
        data = aList[n] if n < len(aList) else None
        g.trace(n, len(aList), repr(data))
        return data
    #@+node:ekr.20170516093009.1: *4* LeoTreeData.is_ancestor_of
    def is_ancestor_of(self, node):
        
        assert isinstance(node, LeoTreeData), repr(node)
        parent = node._parent
        while parent:
            if parent == self:
                return True
            else:
                parent = parent._parent
        return False
    #@+node:ekr.20170516085427.1: *4* LeoTreeData.overrides
    # Don't use weakrefs!
    #@+node:ekr.20170518103807.6: *5* LeoTreeData.find_depth
    def find_depth(self, d=0):
        if native:
            p = self.content
            n = p.level()
            # g.trace('LeoTreeData', n, p.h)
            return n
        else:
            parent = self.get_parent()
            while parent:
                d += 1
                parent = parent.get_parent()
            return d
    #@+node:ekr.20170516085427.2: *5* LeoTreeData.get_children
    def get_children(self):
        
        if native:
            p = self.content
            return p.children()
        else:
            return self._children
    #@+node:ekr.20170518103807.11: *5* LeoTreeData.get_parent
    def get_parent(self):
        # g.trace('LeoTreeData', g.callers())
        if native:
            p = self.content
            return p.parent()
        else:
            return self._parent
    #@+node:ekr.20170516085427.3: *5* LeoTreeData.get_tree_as_list
    def get_tree_as_list(self): # only_expanded=True, sort=None, key=None):
        '''
        Called only from LeoMLTree.values._getValues.
        
        Return the result of converting this node and its *visible* descendants
        to a list of LeoTreeData nodes.
        '''
        trace = False
        assert g.callers(1) == '_getValues', g.callers()
        aList = [z for z in self.walk_tree(only_expanded=True)]
        if trace: g.trace('LeoTreeData', len(aList))
        return aList
    #@+node:ekr.20170516085427.4: *5* LeoTreeData.new_child
    def new_child(self, *args, **keywords):

        if self.CHILDCLASS:
            cld = self.CHILDCLASS
        else:
            cld = type(self)
        child = cld(parent=self, *args, **keywords)
        self._children.append(child)
        return child
    #@+node:ekr.20170516085742.1: *5* LeoTreeData.new_child_at
    def new_child_at(self, index, *args, **keywords):
        '''Same as new_child, with insert(index, c) instead of append(c)'''
        g.trace('LeoTreeData', g.callers())
        if self.CHILDCLASS:
            cld = self.CHILDCLASS
        else:
            cld = type(self)
        child = cld(parent=self, *args, **keywords)
        self._children.insert(index, child)
        return child
    #@+node:ekr.20170516085427.5: *5* LeoTreeData.remove_child
    def remove_child(self, child):
        
        if native:
            p = self.content
            g.trace('LeoTreeData', p.h, g.callers())
            p.doDelete()
        else:
            self._children = [z for z in self._children if z != child]
                # May be useful when child is cloned.
    #@+node:ekr.20170518103807.21: *5* LeoTreeData.set_content
    def set_content(self, content):

        # g.trace('LeoTreeData', content, g.callers())
        if native:
            if content is None:
                self.content = None
            elif g.isString(content):
                # This is a dummy node, not actually used.
                assert content == '<HIDDEN>', repr(content)
                self.content = content
            else:
                p = content
                assert p and isinstance(p, leoNodes.Position), repr(p)
                self.content = content.copy()
        else:
            self.content = content
    #@+node:ekr.20170516085427.6: *5* LeoTreeData.set_parent
    def set_parent(self, parent):

        # g.trace('LeoTreeData', parent, g.callers())
        self._parent = parent
        
    #@+node:ekr.20170518103807.24: *5* LeoTreeData.walk_tree (native only)
    if native:

        def walk_tree(self,
            only_expanded=True,
            ignore_root=True,
            sort=None,
            sort_function=None,
        ):
            trace = True
            p = self.content.copy()
                # Never change the stored position!
                # LeoTreeData(p) makes a copy of p.
            if trace: g.trace('LeoTreeData: only_expanded:', only_expanded, p.h)
            if not ignore_root:
                yield self # The hidden root. Probably not needed.
            if only_expanded:
                while p:
                    if p.has_children() and p.isExpanded():
                        p.moveToFirstChild()
                        yield LeoTreeData(p)
                    elif p.next():
                        p.moveToNext()
                        yield LeoTreeData(p)
                    elif p.parent():
                        p.moveToParent()
                        yield LeoTreeData(p)
                    else:
                        return # raise StopIteration
            else:
                while p:
                    yield LeoTreeData(p)
                    p.moveToThreadNext()
                    
    # else use the base TreeData.walk_tree method.
    #@-others
#@+node:ekr.20170508085942.1: *3* class LeoTreeLine (npyscreen.TreeLine)
class LeoTreeLine(npyscreen.TreeLine):
    '''A editable TreeLine class.'''

    def __init__(self, *args, **kwargs):
        
        # g.trace('LeoTreeLine', *args, **kwargs)
        super(LeoTreeLine, self).__init__(*args, **kwargs)
        # Done in TreeLine.init:
            # self._tree_real_value   = None
                # A weakproxy to LeoTreeData.
            # self._tree_ignore_root  = None
            # self._tree_depth        = False
            # self._tree_sibling_next = False
            # self._tree_has_children = False
            # self._tree_expanded     = True
            # self._tree_last_line    = False
            # self._tree_depth_next   = False
            # self.safe_depth_display = False
            # self.show_v_lines       = True
        self.set_handlers()
        
    def __repr__(self):
        val = self._tree_real_value
        if native:
            p = val and val.content
            if p is not None:
                assert p and isinstance(p, leoNodes.Position), repr(p)
            return '<LeoTreeLine: %s>' % (p.h if p else 'None')
        else:
            return '<LeoTreeLine: %s>' % (val.content if val else 'None')
        
    __str__ = __repr__

    #@+others
    #@+node:ekr.20170514104550.1: *4* LeoTreeLine._get_string_to_print
    def _get_string_to_print(self):
        
        # From TextfieldBase.
        if native:
            # g.trace('LeoTreeLine: value:', repr(self.value))
            if self.value:
                assert isinstance(self.value, LeoTreeData)
                p = self.value.content
                assert p and isinstance(p, leoNodes.Position), repr(p)
                return p.h
            else:
                return ''
        else:
            s = self.value.content if self.value else None
        # g.trace(repr(s))
        return g.toUnicode(s) if s else None
    #@+node:ekr.20170522032805.1: *4* LeoTreeLine._print
    def _print(self, left_margin=0):
        '''LeoTreeLine._print. Adapted from TreeLine._print.'''
        # pylint: disable=no-member
        
        def put(char):
            self.parent.curses_pad.addch(
                self.rely, self.relx+self.left_margin,
                ord(char), curses.A_NORMAL)
            self.left_margin += 1
        
        self.left_margin = left_margin
        self.parent.curses_pad.bkgdset(' ',curses.A_NORMAL)
        if native:
            c = getattr(self, 'leo_c', None)
            val = self._tree_real_value
            p = val and val.content
            if not p: return # sartup.
            self.left_margin += 2*p.level()
            if p.hasChildren():
                put('-' if p.isExpanded() else '+')
            else:
                put (' ')
            put(':')
            put('*' if c and p == c.p else ' ')
            put('C' if p and p.isCloned() else ' ')
            put('M' if p and p.isMarked() else ' ')
            put('T' if p and p.b.strip() else ' ')
            put(':')
        else:
            self.left_margin += self._print_tree(self.relx)
        # Now draw the actual line.
        if self.highlight:
            self.parent.curses_pad.bkgdset(' ',curses.A_STANDOUT)
        # This draws the actual line.
        super(npyscreen.TreeLine, self)._print()
            # TextfieldBase._print
    #@+node:ekr.20170514183049.1: *4* LeoTreeLine.display_value
    def display_value(self, vl):
        
        # vl is a LeoTreeData.
        if native:
            p = vl.content
            assert p and isinstance(p, leoNodes.Position), repr(p)
            return p.h
        else:
            return vl.content if vl else ''
    #@+node:ekr.20170510210908.1: *4* LeoTreeLine.edit
    def edit(self):
        """Allow the user to edit the widget: ie. start handling keypresses."""
        # g.trace('==== LeoTreeLine')
        self.editing = True
        # self._pre_edit()
        self.highlight = True
        self.how_exited = False
        # self._edit_loop()
        old_parent_editing = self.parent.editing
        self.parent.editing = True
        while self.editing and self.parent.editing:
            self.display()
            self.get_and_use_key_press()
                # A base TreeLine method.
        self.parent.editing = old_parent_editing
        self.editing = False
        self.how_exited = True
        # return self._post_edit()
        self.highlight = False
        self.update()
    #@+node:ekr.20170508130016.1: *4* LeoTreeLine.handlers
    #@+node:ekr.20170508130946.1: *5* LeoTreeLine.h_cursor_beginning
    def h_cursor_beginning(self, ch):

        self.cursor_position = 0
    #@+node:ekr.20170508131043.1: *5* LeoTreeLine.h_cursor_end
    def h_cursor_end(self, ch):
        
        # self.value is a LeoTreeData.
        self.cursor_position = max(0, len(self.value.content)-1)
    #@+node:ekr.20170508130328.1: *5* LeoTreeLine.h_cursor_left
    def h_cursor_left(self, input):
        
        self.cursor_position = max(0, self.cursor_position -1)
    #@+node:ekr.20170508130339.1: *5* LeoTreeLine.h_cursor_right
    def h_cursor_right(self, input):

        self.cursor_position += 1

    #@+node:ekr.20170508130349.1: *5* LeoTreeLine.h_delete_left (done)
    def h_delete_left(self, input):

        # self.value is a LeoTreeData.
        n = self.cursor_position
        if native:
            p = self.value.content
            assert p and isinstance(p, leoNodes.Position), repr(p)
            s = p.h
            if 0 <= n <= len(s):
                p.h = s[:n] + s[n+1:]
        else:
            s = self.value.content
            if 0 <= n <= len(s):
                self.value.content = s[:n] + s[n+1:]
        self.cursor_position -= 1
    #@+node:ekr.20170510212007.1: *5* LeoTreeLine.h_end_editing (test)
    def h_end_editing(self, ch):

        # g.trace('LeoTreeLine', ch)
        c = self.leo_c
        c.endEditing()
        self.editing = False
        self.how_exited = None
    #@+node:ekr.20170508125632.1: *5* LeoTreeLine.h_insert (done)
    def h_insert(self, i):

        # self.value is a LeoTreeData.
        n = self.cursor_position + 1
        if native:
            p = self.value.content
            s = p.h
            p.h = s[:n] + chr(i) + s[n:]
        else:
            s = self.value.content
            self.value.content = s[:n] + chr(i) + s[n:]
        self.cursor_position += 1
    #@+node:ekr.20170508130025.1: *5* LeoTreeLine.set_handlers
    #@@nobeautify

    def set_handlers(self):
        
        # pylint: disable=no-member
        # Override *all* other complex handlers.
        self.complex_handlers = (
            (curses.ascii.isprint, self.h_insert),
        )
        self.handlers.update({
            curses.ascii.ESC:       self.h_end_editing,
            curses.ascii.NL:        self.h_end_editing,
            curses.ascii.LF:        self.h_end_editing,
            curses.KEY_HOME:        self.h_cursor_beginning,  # 262
            curses.KEY_END:         self.h_cursor_end,        # 358.
            curses.KEY_LEFT:        self.h_cursor_left,
            curses.KEY_RIGHT:       self.h_cursor_right,
            curses.ascii.BS:        self.h_delete_left,
            curses.KEY_BACKSPACE:   self.h_delete_left,
        })
    #@+node:ekr.20170519023802.1: *4* LeoTreeLine.when_check_value_changed
    if native:
        
        def when_check_value_changed(self):
            "Check whether the widget's value has changed and call when_valued_edited if so."
            if hasattr(self, 'parent_widget'):
                self.parent_widget.when_value_edited()
                self.parent_widget._internal_when_value_edited()
            return True

    #@-others
#@-others
#@-<< forward reference classes >>
#@+others
#@+node:ekr.20170501043944.1: **   top-level functions
#@+node:ekr.20170419094705.1: *3* init (cursesGui2.py)
def init():
    '''
    top-level init for cursesGui2.py pseudo-plugin.
    This plugin should be loaded only from leoApp.py.
    '''
    if g.app.gui:
        if not g.app.unitTesting:
            s = "Can't install text gui: previous gui installed"
            g.es_print(s, color="red")
        return False
    else:
        return curses and not g.app.gui and not g.app.unitTesting
            # Not Ok for unit testing!
#@+node:ekr.20170501032705.1: *3* leoGlobals replacements
# CGui.init_logger monkey-patches leoGlobals with these functions.
#@+node:ekr.20170430112645.1: *4* es
def es(*args, **keys):
    '''Monkey-patch for g.es.'''
    d = {
        'color': None,
        'commas': False,
        'newline': True,
        'spaces': True,
        'tabName': 'Log',
    }
    d = g.doKeywordArgs(keys, d)
    color = d.get('color')
    s = g.translateArgs(args, d)
    if isinstance(g.app.gui, LeoCursesGui):
        if g.app.gui.log_inited:
            g.app.gui.log.put(s, color=color)
        else:
            g.app.gui.wait_list.append((s, color),)
    # else: logging.info(' KILL: %r' % s)
#@+node:ekr.20170501043411.1: *4* pr
def pr(*args, **keys):
    '''Monkey-patch for g.pr.'''
    d = {'commas': False, 'newline': True, 'spaces': True}
    d = g.doKeywordArgs(keys, d)
    s = g.translateArgs(args, d)
    for line in g.splitLines(s):
        logging.info('   pr: %s' % (line.rstrip()))
#@+node:ekr.20170429165242.1: *4* trace
def trace(*args, **keys):
    '''Monkey-patch for g.trace.'''
    d = {
        'align': 0,
        'before': '',
        'newline': True,
        'caller_level': 1,
        'noname': False,
    }
    d = g.doKeywordArgs(keys, d)
    align = d.get('align', 0)
    caller_level = d.get('caller_level', 1)
    # Compute the caller name.
    if d.get('noname'):
        name = ''
    else:
        try: # get the function name from the call stack.
            f1 = sys._getframe(caller_level) # The stack frame, one level up.
            code1 = f1.f_code # The code object
            name = code1.co_name # The code name
        except Exception:
            name = g.shortFileName(__file__)
        if name == '<module>':
            name = g.shortFileName(__file__)
        if name.endswith('.pyc'):
            name = name[: -1]
    # Pad the caller name.
    if align != 0 and len(name) < abs(align):
        pad = ' ' * (abs(align) - len(name))
        if align > 0: name = name + pad
        else: name = pad + name
    # Munge *args into s.
    result = [name] if name else []
    for arg in args:
        if g.isString(arg):
            pass
        elif g.isBytes(arg):
            arg = g.toUnicode(arg)
        else:
            arg = repr(arg)
        if result:
            result.append(" " + arg)
        else:
            result.append(arg)
    # s = d.get('before') + ''.join(result)
    s = ''.join(result)
    logging.info('trace: %s' % s.rstrip())
#@+node:ekr.20170524123950.1: ** Gui classes
#@+node:ekr.20170419094731.1: *3* class LeoCursesGui (leoGui.LeoGui)
class LeoCursesGui(leoGui.LeoGui):
    '''
    Leo's curses gui wrapper.
    This is g.app.gui, when --gui=curses.
    '''

    def __init__(self):
        '''Ctor for the CursesGui class.'''
        leoGui.LeoGui.__init__(self, 'curses')
            # Init the base class.
        self.consoleOnly = False
            # Required attribute.
        self.curses_app = None
            # The singleton LeoApp instance.
        self.curses_form = None
            # The top-level curses Form instance.
            # Form.editw is the widget with focus.
        self.log = None
            # The present log. Used by g.es
        self.log_inited = False
            # True: don't use the wait_list.
        self.wait_list = []
            # Queued log messages.
        self.init_logger()
            # Do this as early as possible.
            # It monkey-patches g.pr and g.trace.
        # g.trace('CursesGui')
        self.top_form = None
            # The top-level form. Set in createCursesTop.
        self.key_handler = KeyHandler()

    #@+others
    #@+node:ekr.20170504112655.1: *4* CGui.clipboard
    # Yes, using Tkinter seems to be the standard way.
    #@+node:ekr.20170504112744.3: *5* CGui.getTextFromClipboard
    def getTextFromClipboard(self):
        '''Get a unicode string from the clipboard.'''
        root = Tk()
        root.withdraw()
        try:
            s = root.clipboard_get()
        except Exception: # _tkinter.TclError:
            s = ''
        root.destroy()
        return g.toUnicode(s)
    #@+node:ekr.20170504112744.2: *5* CGui.replaceClipboardWith
    def replaceClipboardWith(self, s):
        '''Replace the clipboard with the string s.'''
        root = Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(s)
        root.destroy()

    # Do *not* define setClipboardSelection.
    # setClipboardSelection = replaceClipboardWith
    #@+node:ekr.20170502083158.1: *4* CGui.createCursesTop & helpers
    def createCursesTop(self):
        '''Create the top-level curses Form.'''
        trace = False and not g.unitTesting
        # Assert the key relationships required by the startup code.
        assert self == g.app.gui
        c = g.app.log.c
        assert c == g.app.windowList[0].c
        assert isinstance(c.frame, CoreFrame), repr(c.frame)
        if trace:
            g.trace('commanders in g.app.windowList')
            g.printList([z.c.shortFileName() for z in g.app.windowList])
        # Create the top-level form.
        self.curses_form = form = LeoForm(name = "Welcome to Leo")
            # This call clears the screen.
        self.createCursesLog(c, form)
        self.createCursesTree(c, form)
        self.createCursesBody(c, form)
        self.createCursesMinibuffer(c, form)
        # g.es(form)
        return form
    #@+node:ekr.20170502084106.1: *5* CGui.createCursesBody
    def createCursesBody(self, c, form):
        '''
        Create the curses body widget in the given curses Form.
        Populate it with c.p.b.
        '''
        trace = False
        box = form.add(
            npyscreen.MultiLineEditableBoxed,
            max_height=8, # Subtract 4 lines
            name='Body Pane',
            footer="Press i or o to insert text", 
            values=g.splitLines(c.p.b), 
            slow_scroll=True,
        )
        assert isinstance(box, npyscreen.MultiLineEditableBoxed), repr(box)
        # Get the contained widget.
        widgets = box._my_widgets
        assert len(widgets) == 1
        w = widgets[0]
        if trace: g.trace('\nBODY', w, '\nBOX', box)
        assert isinstance(w, npyscreen.wgmultilineeditable.MultiLineEditable), repr(w)
        # Link and check.
        assert isinstance(c.frame, leoFrame.LeoFrame), repr(c.frame)
            # The generic LeoFrame class
        assert isinstance(c.frame.body, leoFrame.LeoBody), repr(c.frame.body)
            # The generic LeoBody class
        assert c.frame.body.widget is None, repr(c.frame.body.widget)
        c.frame.body.widget = w
        assert c.frame.body.wrapper is None, repr(c.frame.body.wrapper)
        c.frame.body.wrapper = wrapper = BodyWrapper(c, 'body', w)
        # Inject the wrapper for get_focus.
        box.leo_wrapper = wrapper
        w.leo_wrapper = wrapper
            
    #@+node:ekr.20170502083613.1: *5* CGui.createCursesLog
    def createCursesLog(self, c, form):
        '''
        Create the curses log widget in the given curses Form.
        Populate the widget with the queued log messages.
        '''
        box = form.add(
            npyscreen.MultiLineEditableBoxed,
            max_height=8, # Subtract 4 lines
            name='Log Pane',
            footer="Press i or o to insert text", 
            values=[s for s, color in self.wait_list], 
            slow_scroll=False,
        )
        assert isinstance(box, npyscreen.MultiLineEditableBoxed), repr(box)
        # Clear the wait list and disable it.
        self.wait_list = []
        self.log_inited = True
        widgets = box._my_widgets
        assert len(widgets) == 1
        w = widgets[0]
        assert isinstance(w, npyscreen.wgmultilineeditable.MultiLineEditable), repr(w)
        # Link and check...
        assert isinstance(self.log, CoreLog), repr(self.log)
        self.log.widget = w
        assert isinstance(c.frame, leoFrame.LeoFrame), repr(c.frame)
            # The generic LeoFrame class
        c.frame.log.wrapper = wrapper = LogWrapper(c, 'log', w)
        # Inject the wrapper for get_focus.
        box.leo_wrapper = wrapper
        w.leo_wrapper = wrapper
    #@+node:ekr.20170502084249.1: *5* CGui.createCursesMinibuffer
    def createCursesMinibuffer(self, c, form):
        '''Create the curses minibuffer widget in the given curses Form.'''
        trace = False
        
        class MiniBufferBox(npyscreen.BoxTitle):
            '''An npyscreen class representing Leo's minibuffer, with binding.'''
            # pylint: disable=used-before-assignment
            _contained_widget = LeoMiniBuffer
        
        box = form.add(MiniBufferBox, name='Mini-buffer', max_height=3)
        assert isinstance(box, MiniBufferBox)
        # Link and check...
        widgets = box._my_widgets
        assert len(widgets) == 1
        w = widgets[0]
        if trace: g.trace('\nMINI', w, '\nBOX', box)
        assert isinstance(w, LeoMiniBuffer), repr(w)
        assert isinstance(c.frame, CoreFrame), repr(c.frame)
        assert c.frame.miniBufferWidget is None
        wrapper = MiniBufferWrapper(c, 'minibuffer', w)
        assert wrapper.widget == w, repr(wrapper.widget)
        c.frame.miniBufferWidget = wrapper
        # Inject the wrapper for get_focus.
        box.leo_wrapper = wrapper
        w.leo_c = c
        w.leo_wrapper = wrapper
        g.trace(w)
        g.trace(w.leo_wrapper)
    #@+node:ekr.20170502083754.1: *5* CGui.createCursesTree
    def createCursesTree(self, c, form):
        '''Create the curses tree widget in the given curses Form.'''

        class BoxTitleTree(npyscreen.BoxTitle):
            # pylint: disable=used-before-assignment
            _contained_widget = LeoMLTree
            
        hidden_root_node = LeoTreeData(content='<HIDDEN>', ignore_root=True)
        if native:
            pass # cacher created below.
        else:
            for i in range(3):
                node = hidden_root_node.new_child(content='node %s' % (i))
                for j in range(2):
                    child = node.new_child(content='child %s.%s' % (i, j))
                    for k in range(4):
                        grand_child = child.new_child(
                            content='grand-child %s.%s.%s' % (i, j, k))
                        assert grand_child # for pyflakes.
        box = form.add(
            BoxTitleTree,
            max_height=8, # Subtract 4 lines
            name='Tree Pane',
            footer="d: delete node; i: insert node; h: edit (return to end)",
            values=hidden_root_node, 
            slow_scroll=False,
        )
        assert isinstance(box, BoxTitleTree), repr(box)
        # Link and check...
        widgets = box._my_widgets
        assert len(widgets) == 1
        w = leo_tree = widgets[0]
        assert isinstance(w, LeoMLTree), repr(w)
        leo_tree.leo_c = c
        if native:
            leo_tree.values = LeoValues(c=c, tree = leo_tree)
        assert getattr(leo_tree, 'hidden_root_node') is None, leo_tree
        leo_tree.hidden_root_node = hidden_root_node
        assert isinstance(c.frame, leoFrame.LeoFrame), repr(c.frame)
            # CoreFrame is a LeoFrame
        assert isinstance(c.frame.tree, CoreTree), repr(c.frame.tree)
        assert c.frame.tree.canvas is None, repr(c.frame.canvas)
            # A standard ivar, used by Leo's core.
        c.frame.canvas = leo_tree
            # A LeoMLTree.
        assert not hasattr(c.frame.tree, 'treeWidget'), repr(c.frame.tree.treeWidget)
        c.frame.tree.treeWidget = leo_tree
            # treeWidget is an official ivar.
        assert c.frame.tree.widget is None
        c.frame.tree.widget = leo_tree
            # Set CoreTree.widget.
        # Inject the wrapper for get_focus.
        wrapper = c.frame.tree
        assert wrapper
        box.leo_wrapper = wrapper
        w.leo_wrapper = wrapper
    #@+node:ekr.20170419110052.1: *4* CGui.createLeoFrame
    def createLeoFrame(self, c, title):
        '''
        Create a LeoFrame for the current gui.
        Called from Leo's core (c.initObjects).
        '''
        return CoreFrame(c, title)
    #@+node:ekr.20170502103338.1: *4* CGui.destroySelf
    def destroySelf(self):
        '''
        Terminate the curses gui application.
        Leo's core calls this only if the user agrees to terminate the app.
        '''
        sys.exit(0)
    #@+node:ekr.20170502021145.1: *4* CGui.dialogs (to do)
    def dialog_message(self, message):
        if not g.unitTesting:
            for s in g.splitLines(message):
                g.pr(s.rstrip())

    def runAboutLeoDialog(self, c, version, theCopyright, url, email):
        """Create and run Leo's About Leo dialog."""
        if not g.unitTesting:
            g.trace(version)

    def runAskLeoIDDialog(self):
        """Create and run a dialog to get g.app.LeoID."""
        if not g.unitTesting:
            g.trace('not ready yet')

    def runAskOkDialog(self, c, title,
        message=None,
        text="Ok",
    ):
        """Create and run an askOK dialog ."""
        # Potentially dangerous dialog.
        # self.dialog_message(message)
        if g.unitTesting:
            return False
        elif self.curses_app:
            val = utilNotify.notify_confirm(message=message,title=title)
            g.trace(repr(val))
            return val
        else:
            return False

    def runAskOkCancelNumberDialog(self, c, title, message,
        cancelButtonText=None,
        okButtonText=None,
    ):
        """Create and run askOkCancelNumber dialog ."""
        if g.unitTesting:
            return False
        elif self.curses_app:
            g.trace()
            self.dialog_message(message)
            val = utilNotify.notify_ok_cancel(message=message,title=title)
            g.trace(val)
            return val
        else:
            return False

    def runAskOkCancelStringDialog(self, c, title, message,
        cancelButtonText=None,
        okButtonText=None,
        default="",
        wide=False,
    ):
        """Create and run askOkCancelString dialog ."""
        if g.unitTesting:
            return False
        else:
            g.trace()
            self.dialog_message(message)
            val = utilNotify.notify_ok_cancel(message=message,title=title)
            g.trace(val)
            return val

    def runAskYesNoDialog(self, c, title,
        message=None,
        yes_all=False,
        no_all=False,
    ):
        """Create and run an askYesNo dialog."""
        if g.unitTesting:
            return False
        else:
            val = utilNotify.notify_ok_cancel(message=message,title=title)
            return 'yes' if val else 'no'

    def runAskYesNoCancelDialog(self, c, title,
        message=None,
        yesMessage="Yes",
        noMessage="No",
        yesToAllMessage=None,
        defaultButton="Yes",
        cancelMessage=None,
    ):
        """Create and run an askYesNoCancel dialog ."""
        if g.unitTesting:
            return False
        else:
            self.dialog_message(message)
        
    def runOpenFileDialog(self, c, title, filetypes, defaultextension, multiple=False, startpath=None):
        if not g.unitTesting:
            g.trace(title)

    def runPropertiesDialog(self,
        title='Properties',
        data=None,
        callback=None,
        buttons=None,
    ):
        """Dispay a modal TkPropertiesDialog"""
        if not g.unitTesting:
            g.trace(title)
        
    def runSaveFileDialog(self, c, initialfile, title, filetypes, defaultextension):
        if not g.unitTesting:
            g.trace(title)
    #@+node:ekr.20170430114709.1: *4* CGui.do_key
    def do_key(self, ch_i):
        
        return self.key_handler.do_key(ch_i)
    #@+node:ekr.20170522005855.1: *4* CGui.event_generate
    def event_generate(self, c, char, shortcut, w):

        event = KeyEvent(
            c=c,
            char=char,
            event=g.NullObject(),
            shortcut=shortcut,
            w=w,
        )
        c.k.masterKeyHandler(event)
        c.outerUpdate()
    #@+node:ekr.20170514060742.1: *4* CGui.fonts
    def getFontFromParams(self, family, size, slant, weight, defaultSize=12):
        # g.trace('CursesGui', g.callers())
        return None
    #@+node:ekr.20170502101347.1: *4* CGui.get/set_focus
    def get_focus(self, c=None, raw=False, at_idle=False):
        '''
        Return the Leo wrapper for the npyscreen widget that is being edited.
        '''
        # Careful during startup.
        editw = getattr(g.app.gui.curses_form, 'editw', None)
        if editw is None:
            return None
        widget = self.curses_form._widgets__[editw]
        if hasattr(widget, 'leo_wrapper'):
            return widget.leo_wrapper
        else:
            g.trace('===== no leo_wrapper', widget)
                # At present, HeadWrappers have no widgets.
            return None
            
    set_focus_dict = {}
        # Keys are wrappers, values are npyscreen.widgets.
    set_focus_ok = []
    set_focus_fail = []

    def set_focus(self, c, w):
        trace = False
        trace_cache = False
        # w is a wrapper
        widget = getattr(w, 'widget', None)
        if not widget:
            if trace or not w: g.trace('no widget', repr(w))
            return
        if not isinstance(widget, npyscreen.wgwidget.Widget):
            g.trace('not an npyscreen.Widget', repr(w))
            return
        form = self.curses_form
        d = self.set_focus_dict
        if w in d:
            i = d.get(w)
            if trace and trace_cache and w not in self.set_focus_ok:
                self.set_focus_ok.append(w)
                g.trace('Cached', i, w)
            form.edit_w = i
            if not g.unitTesting:
                form.display()
            return
        for i, widget2 in enumerate(form._widgets__):
            if widget == widget2:
                if trace: g.trace('FOUND', i, widget)
                d [w] = form.editw = i
                if not g.unitTesting:
                    form.display()
                    return
            for j, widget3 in enumerate(getattr(widget2, '_my_widgets', [])):
                if widget == widget3 or repr(widget) == repr(widget3):
                    if trace: g.trace('FOUND INNER', i, j, widget)
                    d [w] = form.editw = i # Not j!?
                    if not g.unitTesting:
                        form.display()
                    return
        if trace and widget not in self.set_focus_fail:
            self.set_focus_fail.append(widget)
            g.trace('Fail\n%r\n%r' % (widget, w))
            ###
                # g.printList(form._widgets__)
                # for outer in form._widgets__:
                    # g.trace('outer:', outer)
                    # if hasattr(outer, '_my_widgets'):
                        # g.printList(outer._my_widgets)
                    # else:
                        # g.trace('no inner widgets')
    #@+node:ekr.20170501032447.1: *4* CGui.init_logger
    def init_logger(self):

        self.rootLogger = logging.getLogger('')
        self.rootLogger.setLevel(logging.DEBUG)
        socketHandler = logging.handlers.SocketHandler(
            'localhost',
            logging.handlers.DEFAULT_TCP_LOGGING_PORT,
        )
        self.rootLogger.addHandler(socketHandler)
        logging.info('-' * 20)
        # Monkey-patch leoGlobals functions.
        g.es = es
        g.pr = pr # Most ouput goes through here, including g.es_exception.
        g.trace = trace
    #@+node:ekr.20170504052119.1: *4* CGui.isTextWrapper
    def isTextWrapper(self, w):
        '''Return True if w is a Text widget suitable for text-oriented commands.'''
        return w and getattr(w, 'supportsHighLevelInterface', None)
    #@+node:ekr.20170504052042.1: *4* CGui.oops
    def oops(self):
        '''Ignore do-nothing methods.'''
        g.pr("CursesGui oops:", g.callers(4), "should be overridden in subclass")
    #@+node:ekr.20170502020354.1: *4* CGui.run
    def run(self):
        '''
        Create and run the top-level curses form.
        
        '''
        self.top_form = self.createCursesTop()
        self.top_form.edit()
    #@+node:ekr.20170419140914.1: *4* CGui.runMainLoop
    def runMainLoop(self):
        '''The curses gui main loop.'''
        # pylint: disable=no-member
        #
        # Do NOT change g.app!
        self.curses_app = LeoApp()
        stdscr = curses.initscr()
        try:
            self.curses_app.run()
                # run calls CApp.main(), which calls CGui.run().
        finally:
            curses.nocbreak()
            stdscr.keypad(0)
            curses.echo()
            curses.endwin()
            g.pr('Exiting Leo...')
    #@+node:ekr.20170510074755.1: *4* CGui.test
    def test(self):
        '''A place to put preliminary tests.'''
    #@-others
#@+node:edward.20170428174322.1: *3* class KeyEvent (object)
class KeyEvent(object):
    '''A gui-independent wrapper for gui events.'''
    #@+others
    #@+node:edward.20170428174322.2: *4* KeyEvent.__init__
    def __init__(self, c, char, event, shortcut, w,
        x=None,
        y=None,
        x_root=None,
        y_root=None,
    ):
        '''Ctor for KeyEvent class.'''
        trace = False
        assert not g.isStroke(shortcut), g.callers()
        stroke = g.KeyStroke(shortcut) if shortcut else None
        if trace: g.trace('KeyEvent: stroke', stroke)
        self.c = c
        self.char = char or ''
        self.event = event
        self.stroke = stroke
        self.w = self.widget = w
        # Optional ivars
        self.x = x
        self.y = y
        # Support for fastGotoNode plugin
        self.x_root = x_root
        self.y_root = y_root
    #@+node:edward.20170428174322.3: *4* KeyEvent.__repr__
    def __repr__(self):
        return 'KeyEvent: stroke: %s, char: %s, w: %s' % (
            repr(self.stroke), repr(self.char), repr(self.w))
    #@+node:edward.20170428174322.4: *4* KeyEvent.get & __getitem__
    def get(self, attr):
        '''Compatibility with g.bunch: return an attr.'''
        return getattr(self, attr, None)

    def __getitem__(self, attr):
        '''Compatibility with g.bunch: return an attr.'''
        return getattr(self, attr, None)
    #@+node:edward.20170428174322.5: *4* KeyEvent.type
    def type(self):
        return 'KeyEvent'
    #@-others
#@+node:ekr.20170430114840.1: *3* class KeyHandler (object)
class KeyHandler (object):

    #@+others
    #@+node:ekr.20170430114930.1: *4* CKey.do_key & helpers
    def do_key(self, ch_i):
        '''
        Handle a key event by calling k.masterKeyHandler.
        Return True if the event was completely handled.
        '''
        #  This is a rewrite of LeoQtEventFilter code.
        c = g.app.log and g.app.log.c
        if not c:
            return True # We are shutting down.
        elif self.is_key_event(ch_i):
            char, shortcut = self.to_key(ch_i)
            if shortcut:
                try:
                    w = c.frame.body.wrapper
                    event = self.create_key_event(c, w, char, shortcut)
                    c.k.masterKeyHandler(event)
                except Exception:
                    g.es_exception()
            return bool(shortcut)
        else:
            return False
    #@+node:ekr.20170430115131.4: *5* CKey.char_to_tk_name
    tk_dict = {
        # Part 1: same as g.app.guiBindNamesDict
        "&": "ampersand",
        "^": "asciicircum",
        "~": "asciitilde",
        "*": "asterisk",
        "@": "at",
        "\\": "backslash",
        "|": "bar",
        "{": "braceleft",
        "}": "braceright",
        "[": "bracketleft",
        "]": "bracketright",
        ":": "colon",
        ",": "comma",
        "$": "dollar",
        "=": "equal",
        "!": "exclam",
        ">": "greater",
        "<": "less",
        "-": "minus",
        "#": "numbersign",
        '"': "quotedbl",
        "'": "quoteright",
        "(": "parenleft",
        ")": "parenright",
        "%": "percent",
        ".": "period",
        "+": "plus",
        "?": "question",
        "`": "quoteleft",
        ";": "semicolon",
        "/": "slash",
        " ": "space",
        "_": "underscore",
        # Curses.
        ### Qt
            # # Part 2: special Qt translations.
            # 'Backspace': 'BackSpace',
            # 'Backtab': 'Tab', # The shift mod will convert to 'Shift+Tab',
            # 'Esc': 'Escape',
            # 'Del': 'Delete',
            # 'Ins': 'Insert', # was 'Return',
            # # Comment these out to pass the key to the QTextWidget.
            # # Use these to enable Leo's page-up/down commands.
            # 'PgDown': 'Next',
            # 'PgUp': 'Prior',
            # # New entries.  These simplify code.
            # 'Down': 'Down', 'Left': 'Left', 'Right': 'Right', 'Up': 'Up',
            # 'End': 'End',
            # 'F1': 'F1', 'F2': 'F2', 'F3': 'F3', 'F4': 'F4', 'F5': 'F5',
            # 'F6': 'F6', 'F7': 'F7', 'F8': 'F8', 'F9': 'F9',
            # 'F10': 'F10', 'F11': 'F11', 'F12': 'F12',
            # 'Home': 'Home',
            # # 'Insert':'Insert',
            # 'Return': 'Return',
            # 'Tab': 'Tab',
            # # 'Tab':'\t', # A hack for QLineEdit.
            # # Unused: Break, Caps_Lock,Linefeed,Num_lock
    }

    def char_to_tk_name(self, ch):
        return self.tk_dict.get(ch, ch)
    #@+node:ekr.20170430115131.2: *5* CKey.create_key_event
    def create_key_event(self, c, w, ch, shortcut):
        trace = False
        # Last-minute adjustments...
        if shortcut == 'Return':
            ch = '\n' # Somehow Qt wants to return '\r'.
        elif shortcut == 'Escape':
            ch = 'Escape'
        # Switch the Shift modifier to handle the cap-lock key.
        if isinstance(ch, int):
            g.trace('can not happen: ch: %r shortcut: %r' % (ch, shortcut))
        elif (
            ch and len(ch) == 1 and
            shortcut and len(shortcut) == 1 and
            ch.isalpha() and shortcut.isalpha()
        ):
            if ch != shortcut:
                if trace: g.trace('caps-lock')
                shortcut = ch
        # Patch provided by resi147.
        # See the thread: special characters in MacOSX, like '@'.
        # Alt keys apparently never generated.
            # if sys.platform.startswith('darwin'):
                # darwinmap = {
                    # 'Alt-Key-5': '[',
                    # 'Alt-Key-6': ']',
                    # 'Alt-Key-7': '|',
                    # 'Alt-slash': '\\',
                    # 'Alt-Key-8': '{',
                    # 'Alt-Key-9': '}',
                    # 'Alt-e': '€',
                    # 'Alt-l': '@',
                # }
                # if tkKey in darwinmap:
                    # shortcut = darwinmap[tkKey]
        if trace: g.trace('ch: %r, shortcut: %r' % (ch, shortcut))
        import leo.core.leoGui as leoGui
        return leoGui.LeoKeyEvent(
            c=c,
            char=ch,
            event={'c': c, 'w': w},
            shortcut=shortcut,
            w=w, x=0, y=0, x_root=0, y_root=0,
        )
    #@+node:ekr.20170430115030.1: *5* CKey.is_key_event
    def is_key_event(self, ch_i):
        # pylint: disable=no-member
        return ch_i not in (curses.KEY_MOUSE,)
    #@+node:ekr.20170430115131.3: *5* CKey.to_key
    def to_key(self, i):
        '''Convert int i to a char and shortcut.'''
        trace = False
        a = curses.ascii
        char, shortcut = '', ''
        s = a.unctrl(i)
        if i <= 32:
            d = {
                8:'Backspace',  9:'Tab',
                10:'Return',    13:'Linefeed',
                27:'Escape',    32: ' ',
            }
            shortcut = d.get(i, '')
            # All real ctrl keys lie between 1 and 26.
            if shortcut and shortcut != 'Escape':
                char = chr(i)
            elif len(s) >= 2 and s.startswith('^'):
                shortcut = 'Ctrl+' + self.char_to_tk_name(s[1:].lower())
        elif i == 127:
            pass
        elif i < 128:
            char = shortcut = chr(i)
            if char.isupper():
                shortcut = 'Shift+' + char
            else:
                shortcut = self.char_to_tk_name(char)
        elif 265 <= i <= 276:
            # Special case for F-keys
            shortcut = 'F%s' % (i-265+1)
        elif i == 351:
            shortcut = 'Shift+Tab'
        elif s.startswith('\\x'):
            pass
        elif len(s) >= 3 and s.startswith('!^'):
            shortcut = 'Alt+' + self.char_to_tk_name(s[2:])
        else:
            pass
        if trace: g.trace('i: %s s: %s char: %r shortcut: %r' % (i, s, char, shortcut))
        return char, shortcut
    #@-others
#@+node:ekr.20170524124010.1: ** Leo widget classes
# Most are subclasses Leo's base gui classes.
# All classes have a "c" ivar.
#@+node:ekr.20170501024433.1: *3* class CoreBody (leoFrame.LeoBody)
class CoreBody (leoFrame.LeoBody):
    '''
    A class that represents curses body pane.
    This is c.frame.body.
    '''
    
    def __init__(self, c):
        
        # g.trace('CoreBody', c.frame)
        leoFrame.LeoBody.__init__(self, frame=c.frame, parentFrame=None)
            # Init the base class.
        self.c = c
        self.colorizer = leoFrame.NullColorizer(c)
        self.widget = None
        self.wrapper = None # Set in createCursesBody.
#@+node:ekr.20170419105852.1: *3* class CoreFrame (leoFrame.LeoFrame)
class CoreFrame (leoFrame.LeoFrame):
    '''The LeoFrame when --gui=curses is in effect.'''
    
    #@+others
    #@+node:ekr.20170501155347.1: *4* CFrame.birth
    def __init__ (self, c, title):
        
        # g.trace('CoreFrame', c.shortFileName())
        leoFrame.LeoFrame.instances += 1 # Increment the class var.
        leoFrame.LeoFrame.__init__(self, c, gui=g.app.gui)
            # Init the base class.
        assert c and self.c == c
        c.frame = self # Bug fix: 2017/05/10.
        self.log = CoreLog(c)
        g.app.gui.log = self.log
        self.title = title
        # Standard ivars.
        self.ratio = self.secondary_ratio = 0.0
        # Widgets
        self.top = TopFrame(c)
        self.body = CoreBody(c)
        self.menu = CoreMenu(c)
        self.miniBufferWidget = None
            # Set later.
        self.statusLine = g.NullObject()
        assert self.tree is None, self.tree
        self.tree = CoreTree(c)
        ### ===============
            # Official ivars...
            # self.iconBar = None
            # self.iconBarClass = None # self.QtIconBarClass
            # self.initComplete = False # Set by initCompleteHint().
            # self.minibufferVisible = True
            # self.statusLineClass = None # self.QtStatusLineClass
            #
            # Config settings.
            # self.trace_status_line = c.config.getBool('trace_status_line')
            # self.use_chapters = c.config.getBool('use_chapters')
            # self.use_chapter_tabs = c.config.getBool('use_chapter_tabs')
            #
            # self.set_ivars()
            #
            # "Official ivars created in createLeoFrame and its allies.
            # self.bar1 = None
            # self.bar2 = None
            # self.f1 = self.f2 = None
            # self.findPanel = None # Inited when first opened.
            # self.iconBarComponentName = 'iconBar'
            # self.iconFrame = None
            # self.canvas = None
            # self.outerFrame = None
            # self.statusFrame = None
            # self.statusLineComponentName = 'statusLine'
            # self.statusText = None
            # self.statusLabel = None
            # self.top = None # This will be a class Window object.
            # Used by event handlers...
            # self.controlKeyIsDown = False # For control-drags
            # self.isActive = True
            # self.redrawCount = 0
            # self.wantedWidget = None
            # self.wantedCallbackScheduled = False
            # self.scrollWay = None
    #@+node:ekr.20170420163932.1: *5* CFrame.finishCreate (more work may be needed)
    def finishCreate(self):
        # g.trace('CoreFrame', self.c.shortFileName())
        c = self.c
        g.app.windowList.append(self)
        c.findCommands.ftm = g.NullObject()
        self.createFirstTreeNode()
            # Call the base-class method.

        ### Not yet.
            # c = self.c
            # assert c
            # self.top = g.app.gui.frameFactory.createFrame(self)
            # self.createIconBar() # A base class method.
            # self.createSplitterComponents()
            # self.createStatusLine() # A base class method.
            # self.miniBufferWidget = qt_text.QMinibufferWrapper(c)
            # c.bodyWantsFocus()
    #@+node:ekr.20170524145750.1: *4* CFrame.cmd (decorator)
    def cmd(name):
        '''Command decorator for the LeoFrame class.'''
        # pylint: disable=no-self-argument
        return g.new_cmd_decorator(name, ['c', 'frame',])
    #@+node:ekr.20170501161029.1: *4* CFrame.do nothings
    def bringToFront(self):
        pass
        
    def contractPane(self, event=None):
        pass

    def deiconify(self):
        pass
            
    def destroySelf(self):
        pass



    def get_window_info(self):
        return 0, 0, 0, 0

    def iconify(self):
        pass

    def lift(self):
        pass
        
    def getShortCut(self, *args, **kwargs):
        return None

    def getTitle(self):
        return self.title
        
    def minimizeAll(self, event=None):
        pass
        
    def oops(self):
        '''Ignore do-nothing methods.'''
        g.pr("CoreFrame oops:", g.callers(4), "should be overridden in subclass")

    def resizePanesToRatio(self, ratio, secondary_ratio):
        '''Resize splitter1 and splitter2 using the given ratios.'''
        # self.divideLeoSplitter1(ratio)
        # self.divideLeoSplitter2(secondary_ratio)
        
    def resizeToScreen(self, event=None):
        pass
        
    def setInitialWindowGeometry(self):
        pass

    def setTitle(self, title):
        self.title = g.toUnicode(title)

    def setTopGeometry(self, w, h, x, y, adjustSize=True):
        pass
        
    def setWrap(self, p):
        pass

    def update(self, *args, **keys):
        pass
    #@+node:ekr.20170524144717.1: *4* CFrame.get_focus
    def getFocus(self):
        
        return g.app.gui.get_focus()
    #@+node:ekr.20170522015906.1: *4* CFrame.pasteText
    @cmd('paste-text')
    def pasteText(self, event=None, middleButton=False):
        '''
        Paste the clipboard into a widget.
        If middleButton is True, support x-windows middle-mouse-button easter-egg.
        '''
        trace = False and not g.unitTesting
        c = self.c
        w = event and event.widget
        wrapper = getattr(w, 'leo_wrapper')
        wname = c.widget_name(wrapper)
        if not wrapper:
            g.trace('no wrapper', repr(w))
            return
        i, j = oldSel = wrapper.getSelectionRange()
            # Returns insert point if no selection.
        oldText = wrapper.getAllText()
        s = g.app.gui.getTextFromClipboard()
        s = g.toUnicode(s)
        if trace: g.trace('wname',wname, 'len(s)', len(s))
        singleLine = wname.startswith('head') or wname.startswith('minibuffer')
        if singleLine:
            # Strip trailing newlines so the truncation doesn't cause confusion.
            while s and s[-1] in ('\n', '\r'):
                s = s[: -1]
        # Update the widget.
        if i != j:
            wrapper.delete(i, j)
        wrapper.insert(i, s)
        wrapper.see(i + len(s) + 2)
        if wname.startswith('body'):
            c.frame.body.onBodyChanged('Paste', oldSel=oldSel, oldText=oldText)
        elif wname.startswith('head'):
            c.frame.tree.onHeadChanged(
                wrapper.p, 'Paste',
                s=wrapper.getAllText(),
            )
                # New for Curses gui.

    OnPasteFromMenu = pasteText
    #@-others
#@+node:ekr.20170419143731.1: *3* class CoreLog (leoFrame.LeoLog)
class CoreLog (leoFrame.LeoLog):
    '''
    A class that represents curses log pane.
    This is c.frame.log.
    '''
    
    #@+others
    #@+node:ekr.20170419143731.4: *4* CLog.__init__
    def __init__(self, c):
        '''Ctor for CLog class.'''
        # g.trace('CoreLog')
        leoFrame.LeoLog.__init__(self,
            frame = None,
            parentFrame = None,
        )
            # Init the base class.
        self.c = c
        self.enabled = True
            # Required by Leo's core.
        self.isNull = False
            # Required by Leo's core.
        self.widget = None
            # The npyscreen log widget. Queue all output until set.
            # Set in CApp.main.
        #
        self.contentsDict = {}
            # Keys are tab names.  Values are widgets.
        self.logDict = {}
            # Keys are tab names text widgets.  Values are the widgets.
        self.tabWidget = None
    #@+node:ekr.20170419143731.2: *4*  CLog.cmd (decorator)
    def cmd(name):
        '''Command decorator for the c.frame.log class.'''
        # pylint: disable=no-self-argument
        return g.new_cmd_decorator(name, ['c', 'frame', 'log'])
    #@+node:ekr.20170419143731.7: *4* CLog.clearLog
    @cmd('clear-log')
    def clearLog(self, event=None):
        '''Clear the log pane.'''
        # w = self.logCtrl.widget # w is a QTextBrowser
        # if w:
            # w.clear()
    #@+node:ekr.20170420035717.1: *4* CLog.enable/disable
    def disable(self):
        self.enabled = False

    def enable(self, enabled=True):
        self.enabled = enabled
    #@+node:ekr.20170420041119.1: *4* CLog.finishCreate
    def finishCreate(self):
        '''CoreLog.finishCreate.'''
        pass
    #@+node:ekr.20170513183826.1: *4* CLog.isLogWidget
    def isLogWidget(self, w):
        return w == self or w in list(self.contentsDict.values())
    #@+node:ekr.20170513184115.1: *4* CLog.orderedTabNames
    def orderedTabNames(self, LeoLog=None): # Unused: LeoLog
        '''Return a list of tab names in the order in which they appear in the QTabbedWidget.'''
        return []
        ### w = self.tabWidget
        ### return [w.tabText(i) for i in range(w.count())]
    #@+node:ekr.20170419143731.15: *4* CLog.put
    def put(self, s, color=None, tabName='Log', from_redirect=False):
        '''All output to the log stream eventually comes here.'''
        c = self.c
        w = self.widget
            # This is the actual MultiLine widget
        if not c or not c.exists:
            # logging.info('CLog.put: no c: %r' % s)
            pass
        elif w:
            assert isinstance(w, npyscreen. MultiLineEditable), repr(w)
            w.values.append(s)
            w.update()
        else:
            pass
            # logging.info('CLog.put no w: %r' % s)
    #@+node:ekr.20170419143731.16: *4* CLog.putnl
    def putnl(self, tabName='Log'):
        '''Put a newline to the Qt log.'''
        # This is not called normally.
        # print('CLog.put: %s' % g.callers())
        if g.app.quitting:
            return
        # if tabName:
            # self.selectTab(tabName)
        # w = self.logCtrl.widget
        # if w:
            # sb = w.horizontalScrollBar()
            # pos = sb.sliderPosition()
            # # Not needed!
                # # contents = w.toHtml()
                # # w.setHtml(contents + '\n')
            # w.moveCursor(QtGui.QTextCursor.End)
            # sb.setSliderPosition(pos)
            # w.repaint() # Slow, but essential.
        # else:
            # # put s to logWaiting and print  a newline
            # g.app.logWaiting.append(('\n', 'black'),)
    #@-others
#@+node:ekr.20170419111515.1: *3* class CoreMenu (leoMenu.LeoMenu)
class CoreMenu (leoMenu.LeoMenu):

    def __init__ (self, c):
        
        dummy_frame = g.Bunch(c=c)
        leoMenu.LeoMenu.__init__(self, dummy_frame)
        self.c = c
        self.d = {}

    def oops(self):
        '''Ignore do-nothing methods.'''
        # g.pr("CoreMenu oops:", g.callers(4), "should be overridden in subclass")

        
#@+node:ekr.20170501024424.1: *3* class CoreTree (leoFrame.LeoTree)
class CoreTree (leoFrame.LeoTree):
    '''
    A class that represents curses tree pane.
    
    This is the c.frame.tree instance.
    '''
        
    #@+others
    #@+node:ekr.20170511111242.1: *4*  CTree.ctor
    class DummyFrame:
        def __init__(self, c):
            self.c = c

    def __init__(self, c):

        dummy_frame = self.DummyFrame(c)
        leoFrame.LeoTree.__init__(self, dummy_frame)
            # Init the base class.
        assert self.c
        assert not hasattr(self, 'widget')
        self.redrawCount = 0 # For unit tests.
        self.widget = None
            # A LeoMLTree set by CGui.createCursesTree.
        # self.setConfigIvars()
        self.setEditPosition(None) # Set positions returned by LeoTree.editPosition()
        # Status flags, for busy()
        self.contracting = False
        self.expanding = False
        self.redrawing = False
        self.selecting = False
    #@+node:ekr.20170511094217.1: *4* CTree.Drawing
    #@+node:ekr.20170511094217.3: *5* CTree.redraw
    def redraw(self, p=None, scroll=True, forceDraw=False):
        '''
        Redraw all visible nodes of the tree.
        Preserve the vertical scrolling unless scroll is True.
        '''
        trace = False and not g.unitTesting
        if g.unitTesting:
            return # There is no need. At present, the tests hang.
        if trace: g.trace(g.callers())
        if self.widget and not self.busy():
            self.redrawCount += 1 # To keep a unit test happy.
            self.widget.update()
    # Compatibility

    full_redraw = redraw
    redraw_now = redraw
    repaint = redraw
    #@+node:ekr.20170511100356.1: *5* CTree.redraw_after...
    def redraw_after_contract(self, p=None):
        self.redraw(p=p, scroll=False)

    def redraw_after_expand(self, p=None):
        self.redraw(p=p)

    def redraw_after_head_changed(self):
        self.redraw()

    def redraw_after_icons_changed(self):
        self.redraw()

    def redraw_after_select(self, p=None):
        '''Redraw the entire tree when an invisible node is selected.'''
        # Prevent the selecting lockout from disabling the redraw.
        oldSelecting = self.selecting
        self.selecting = False
        try:
            if not self.busy():
                self.redraw(p=p, scroll=False)
        finally:
            self.selecting = oldSelecting
        # Do *not* call redraw_after_select here!
    #@+node:ekr.20170511104032.1: *4* CTree.error
    def error(self, s):
        if not g.app.unitTesting:
            g.trace('LeoQtTree Error: %s' % (s), g.callers())
    #@+node:ekr.20170511104533.1: *4* CTree.Event handlers
    #@+node:ekr.20170511104533.10: *5* CTree.busy
    def busy(self):
        '''Return True (actually, a debugging string)
        if any lockout is set.'''
        trace = False
        table = ('contracting','expanding','redrawing','selecting')
        kinds = ','.join([z for z in table if getattr(self, z)])
        if kinds and trace: g.trace(kinds)
        return kinds # Return the string for debugging
    #@+node:ekr.20170511104533.12: *5* CTree.onHeadChanged
    # Tricky code: do not change without careful thought and testing.

    def onHeadChanged(self, p, undoType='Typing', s=None, e=None):
        '''Officially change a headline.'''
        trace = False and not g.unitTesting
        c, u = self.c, self.c.undoer
        if not c.frame.body.wrapper:
            return # Startup.
        w = self.edit_widget(p)
        if c.suppressHeadChanged:
            if trace: g.trace('c.suppressHeadChanged')
            return
        if not w:
            if trace: g.trace('****** no w for p: %s', repr(p))
            return
        ch = '\n' # New in 4.4: we only report the final keystroke.
        if s is None: s = w.getAllText()
        if trace:
            g.trace('*** CoreTree', p and p.h, 's', repr(s))
        #@+<< truncate s if it has multiple lines >>
        #@+node:ekr.20170511104533.13: *6* << truncate s if it has multiple lines >>
        # Remove trailing newlines before warning of truncation.
        while s and s[-1] == '\n':
            s = s[: -1]
        # Warn if there are multiple lines.
        i = s.find('\n')
        if i > -1:
            s = s[: i]
            # if s != oldHead:
                # g.warning("truncating headline to one line")
        limit = 1000
        if len(s) > limit:
            s = s[: limit]
            # if s != oldHead:
                # g.warning("truncating headline to", limit, "characters")
        #@-<< truncate s if it has multiple lines >>
        # Make the change official, but undo to the *old* revert point.
        oldRevert = self.revertHeadline
        changed = s != oldRevert
        self.revertHeadline = s
        p.initHeadString(s)
        if trace: g.trace('changed', changed, 'new', repr(s))
        if g.doHook("headkey1", c=c, p=p, v=p, ch=ch, changed=changed):
            return # The hook claims to have handled the event.
        if changed:
            undoData = u.beforeChangeNodeContents(p, oldHead=oldRevert)
            if not c.changed:
                c.setChanged(True)
            # New in Leo 4.4.5: we must recolor the body because
            # the headline may contain directives.
            ### c.frame.scanForTabWidth(p)
            ### c.frame.body.recolor(p, incremental=True)
            dirtyVnodeList = p.setDirty()
            u.afterChangeNodeContents(p, undoType, undoData,
                dirtyVnodeList=dirtyVnodeList, inHead=True)
        ### if changed:
        ###    c.redraw_after_head_changed()
            # Fix bug 1280689: don't call the non-existent c.treeEditFocusHelper
        g.doHook("headkey2", c=c, p=p, v=p, ch=ch, changed=changed)
    #@+node:ekr.20170511104533.19: *5* CTree.OnPopup & allies (To be deleted)
    # def OnPopup(self, p, event):
        # """Handle right-clicks in the outline.

        # This is *not* an event handler: it is called from other event handlers."""
        # # Note: "headrclick" hooks handled by VNode callback routine.
        # if event:
            # c = self.c
            # c.setLog()
            # if not g.doHook("create-popup-menu", c=c, p=p, v=p, event=event):
                # self.createPopupMenu(event)
            # if not g.doHook("enable-popup-menu-items", c=c, p=p, v=p, event=event):
                # self.enablePopupMenuItems(p, event)
            # if not g.doHook("show-popup-menu", c=c, p=p, v=p, event=event):
                # self.showPopupMenu(event)
        # return "break"
    #@+node:ekr.20170511104533.20: *6* CTree.OnPopupFocusLost
    #@+at
    # On Linux we must do something special to make the popup menu "unpost" if the
    # mouse is clicked elsewhere. So we have to catch the <FocusOut> event and
    # explicitly unpost. In order to process the <FocusOut> event, we need to be able
    # to find the reference to the popup window again, so this needs to be an
    # attribute of the tree object; hence, "self.popupMenu".
    # 
    # Aside: though Qt tries to be muli-platform, the interaction with different
    # window managers does cause small differences that will need to be compensated by
    # system specific application code. :-(
    #@@c
    # 20-SEP-2002 DTHEIN: This event handler is only needed for Linux.

    def OnPopupFocusLost(self, event=None):
        # self.popupMenu.unpost()
        pass
    #@+node:ekr.20170511104533.21: *6* CTree.createPopupMenu
    def createPopupMenu(self, event):
        '''This might be a placeholder for plugins.  Or not :-)'''
    #@+node:ekr.20170511104533.22: *6* CTree.enablePopupMenuItems
    def enablePopupMenuItems(self, v, event):
        """Enable and disable items in the popup menu."""
    #@+node:ekr.20170511104533.23: *6* CTree.showPopupMenu
    def showPopupMenu(self, event):
        """Show a popup menu."""
    #@+node:ekr.20170511104121.1: *4* CTree.Scroll bars
    #@+node:ekr.20170511104121.2: *5* Ctree.getScroll
    def getScroll(self):
        '''Return the hPos,vPos for the tree's scrollbars.'''
        return 0, 0
        # w = self.widget
        # hScroll = w.horizontalScrollBar()
        # vScroll = w.verticalScrollBar()
        # hPos = hScroll.sliderPosition()
        # vPos = vScroll.sliderPosition()
        # return hPos, vPos
    #@+node:ekr.20170511104121.3: *5* Ctree.scrollDelegate
    # def scrollDelegate(self, kind):
        # '''Scroll a QTreeWidget up or down or right or left.
        # kind is in ('down-line','down-page','up-line','up-page', 'right', 'left')
        # '''
        # c = self.c; w = self.widget
        # if kind in ('left', 'right'):
            # hScroll = w.horizontalScrollBar()
            # if kind == 'right':
                # delta = hScroll.pageStep()
            # else:
                # delta = -hScroll.pageStep()
            # hScroll.setValue(hScroll.value() + delta)
        # else:
            # vScroll = w.verticalScrollBar()
            # h = w.size().height()
            # lineSpacing = w.fontMetrics().lineSpacing()
            # n = h / lineSpacing
            # if kind == 'down-half-page': delta = n / 2
            # elif kind == 'down-line': delta = 1
            # elif kind == 'down-page': delta = n
            # elif kind == 'up-half-page': delta = -n / 2
            # elif kind == 'up-line': delta = -1
            # elif kind == 'up-page': delta = -n
            # else:
                # delta = 0; g.trace('bad kind:', kind)
            # val = vScroll.value()
            # # g.trace(kind,n,h,lineSpacing,delta,val)
            # vScroll.setValue(val + delta)
        # c.treeWantsFocus()
    #@+node:ekr.20170511104121.4: *5* Ctree.setH/VScroll
    def setHScroll(self, hPos):
        pass
        # w = self.widget
        # hScroll = w.horizontalScrollBar()
        # hScroll.setValue(hPos)

    def setVScroll(self, vPos):
        pass
        # w = self.widget
        # vScroll = w.verticalScrollBar()
        # vScroll.setValue(vPos)
    #@+node:ekr.20170511105355.1: *4* CTree.Selecting & editing
    #@+node:ekr.20170511105355.4: *5* CTree.edit_widget
    def edit_widget(self, p):
        """Returns the edit widget for position p."""
        return HeadWrapper(c=self.c, name='head', p=p)
    #@+node:ekr.20170511095353.1: *5* CTree.editLabel & helpers
    def editLabel(self, p, selectAll=False, selection=None):
        """Start editing p's headline."""
        if not g.unitTesting: g.trace(p.h)
        return None, None
        ###
            # trace = False and not g.unitTesting
            # if trace: g.trace('all', selectAll, p.h)
            # if self.busy():
                # if trace: g.trace('busy')
                # return
            # c = self.c
            # c.outerUpdate()
                # # Do any scheduled redraw.
                # # This won't do anything in the new redraw scheme.
            # if 1:
                # # Apparently, item is always None below!
                # return None, None
            # else:
                # # item is always None here.
                # item = self.position2item(p)
                # if item:
                    # # if self.use_declutter:
                        # # item.setText(0, item._real_text)
                    # e, wrapper = self.editLabelHelper(item, selectAll, selection)
                # else:
                    # e, wrapper = None, None
                    # self.error('no item for %s' % p)
                # if trace: g.trace('p: %s e: %s' % (p and p.h, e))
                # if e:
                    # self.sizeTreeEditor(c, e)
                    # # A nice hack: just set the focus request.
                    # c.requestedFocusWidget = e
                # return e, wrapper
    #@+node:ekr.20170511095244.22: *6* CTree.editLabelHelper (Never called!)
    # def editLabelHelper(self, item, selectAll=False, selection=None):
        # '''
        # Help nativeTree.editLabel do gui-specific stuff.
        # '''
        # c, vc = self.c, self.c.vimCommands
        # w = self.widget
        # w.setCurrentItem(item)
            # # Must do this first.
            # # This generates a call to onTreeSelect.
        # w.editItem(item)
            # # Generates focus-in event that tree doesn't report.
        # e = w.itemWidget(item, 0) # A QLineEdit.
        # g.trace(repr(e))
        # if e:
            # s = e.text()
            # len_s = len(s)
            # if s == 'newHeadline':
                # selectAll = True
            # if selection:
                # # Fix bug https://groups.google.com/d/msg/leo-editor/RAzVPihqmkI/-tgTQw0-LtwJ
                # # Note: negative lengths are allowed.
                # i, j, ins = selection
                # if ins is None:
                    # start, n = i, abs(i - j)
                    # # This case doesn't happen for searches.
                # elif ins == j:
                    # start, n = i, j - i
                # else:
                    # start, n = j, i - j
            # elif selectAll:
                # start, n, ins = 0, len_s, len_s
            # else: start, n, ins = len_s, 0, len_s
            # e.setObjectName('headline')
            # e.setSelection(start, n)
            # # e.setCursorPosition(ins) # Does not work.
            # e.setFocus()
            # wrapper = self.connectEditorWidget(e, item) # Hook up the widget.
            # if vc and c.vim_mode: #  and selectAll
                # # For now, *always* enter insert mode.
                # if vc.is_text_wrapper(wrapper):
                    # vc.begin_insert_mode(w=wrapper)
                # else:
                    # g.trace('not a text widget!', wrapper)
        # return e, wrapper
    #@+node:ekr.20170522191450.1: *6* CTree.setSelectionHelper
    def setSelectionHelper(self, p, selectAll, selection, wrapper):
        
        s = p.h
        if s == 'newHeadline':
            selectAll = True
        if selection:
            i, j, ins = selection
            if ins is None:
                start, n = i, abs(i - j)
                # This case doesn't happen for searches.
            elif ins == j:
                start, n = i, j - i
            else:
                start, n = j, i - j
        elif selectAll:
            # start, n, ins = 0, len_s, len_s
            start, n = 0, len(s)
        else:
            # start, n, ins = len_s, 0, len_s
            start, n = len(s), 0
        wrapper.setSelection(start, n)
    #@+node:ekr.20170511105355.6: *5* CTree.editPosition
    def editPosition(self):
        c = self.c
        p = c.currentPosition()
        wrapper = self.edit_widget(p)
        return p if wrapper else None
    #@+node:ekr.20170511105355.7: *5* CTree.endEditLabel
    def endEditLabel(self):
        '''Override LeoTree.endEditLabel.

        End editing of the presently-selected headline.'''
        c = self.c
        p = c.currentPosition()
        self.onHeadChanged(p)
    #@+node:ekr.20170511105355.8: *5* CTree.getSelectedPositions
    def getSelectedPositions(self):
        '''This can be called from Leo's core.'''
        return [self.c.p]
    #@+node:ekr.20170511105355.9: *5* CTree.setHeadline
    def setHeadline(self, p, s):
        '''Force the actual text of the headline widget to p.h.'''
        trace = False and not g.unitTesting
        # This is used by unit tests to force the headline and p into alignment.
        if not p:
            if trace: g.trace('*** no p')
            return
        # Don't do this here: the caller should do it.
        # p.setHeadString(s)
        e = self.edit_widget(p)
        assert isinstance(e, HeadWrapper), repr(e)
        e.setAllText(s)
    #@+node:ekr.20170523115818.1: *5* CTree.set_body_text_after_select
    def set_body_text_after_select(self, p, old_p, traceTime, force=False):
        '''Set the text after selecting a node.'''
        c = self.c
        wrapper = c.frame.body.wrapper
        widget = c.frame.body.widget
        # g.trace('==== %d %s' % (len(p.b), p.h))
        c.setCurrentPosition(p)
            # Important: do this *before* setting text,
            # so that the colorizer will have the proper c.p.
        s = p.v.b
        wrapper.setAllText(s)
        widget.values = g.splitLines(s)
        widget.update()
            # Now done after c.p has been changed.
                # p.restoreCursorAndScroll()
    #@-others
#@+node:ekr.20170502093200.1: *3* class TopFrame (object)
class TopFrame (object):
    '''A representation of c.frame.top.'''
    
    def __init__(self, c):
        # g.trace('TopFrame', c)
        self.c = c
        
    def select(self, *args, **kwargs):
        pass # g.trace(args, kwargs)
        
    def findChild(self, *args, **kwargs):
        # Called by nested_splitter.py.
        return g.NullObject() # Required, for now.

    def finishCreateLogPane(self, *args, **kwargs):
        pass # g.trace(args, kwargs)
#@+node:ekr.20170524124449.1: ** Npyscreen classes
# These are subclasses of npyscreen base classes.
# These classes have "leo_c" ivars.
#@+node:ekr.20170420054211.1: *3* class LeoApp (npyscreen.NPSApp)
class LeoApp(npyscreen.NPSApp):
    '''
    The *anonymous* npyscreen application object, created from
    CGui.runMainLoop. This is *not* g.app.
    '''
    
    # No ctor needed.
        # def __init__(self):
            # npyscreen.NPSApp.__init__(self)

    def main(self):
        '''
        Called automatically from the ctor.
        Create and start Leo's singleton npyscreen window.
        '''
        g.app.gui.run()
#@+node:ekr.20170507194035.1: *3* class LeoForm (npyscreen.Form)
class LeoForm (npyscreen.Form):
    
    OK_BUTTON_TEXT = 'Quit Leo'
#@+node:ekr.20170510092721.1: *3* class LeoMiniBuffer (npyscreen.Textfield)
class LeoMiniBuffer(npyscreen.Textfield):
    '''An npyscreen class representing Leo's minibuffer, with binding.''' 
    
    def __init__(self, *args, **kwargs):
        super(LeoMiniBuffer, self).__init__(*args, **kwargs)
        self.leo_c = None # Set later
        self.leo_wrapper = None # Set later.
        self.set_handlers()

    #@+others
    #@+node:ekr.20170510172335.1: *4* LeoMiniBuffer.Handlers
    #@+node:ekr.20170510095136.2: *5* LeoMiniBuffer.h_cursor_beginning
    def h_cursor_beginning(self, ch):

        #g.trace('LeoMiniBuffer', repr(ch))
        self.cursor_position = 0
    #@+node:ekr.20170510095136.3: *5* LeoMiniBuffer.h_cursor_end
    def h_cursor_end(self, ch):
        
        # g.trace('LeoMiniBuffer', repr(ch))
        self.cursor_position = len(self.value)
    #@+node:ekr.20170510095136.4: *5* LeoMiniBuffer.h_cursor_left
    def h_cursor_left(self, ch):
        
        # g.trace('LeoMiniBuffer', repr(ch))
        self.cursor_position = max(0, self.cursor_position -1)
    #@+node:ekr.20170510095136.5: *5* LeoMiniBuffer.h_cursor_right
    def h_cursor_right(self, ch):

        # g.trace('LeoMiniBuffer', repr(ch))
        self.cursor_position = min(len(self.value), self.cursor_position+1)


    #@+node:ekr.20170510095136.6: *5* LeoMiniBuffer.h_delete_left
    def h_delete_left(self, ch):

        # g.trace('LeoMiniBuffer', repr(ch))
        n = self.cursor_position
        s = self.value
        if n == 0:
            # Delete the character under the cursor.
            self.value = s[1:]
        else:
            # Delete the character to the left of the cursor
            self.value = s[:n-1] + s[n:]
            self.cursor_position -= 1
    #@+node:ekr.20170510095136.7: *5* LeoMiniBuffer.h_insert
    def h_insert(self, ch):

        # g.trace('LeoMiniBuffer', ch, self.value)
        n = self.cursor_position + 1
        s = self.value
        self.value = s[:n] + chr(ch) + s[n:]
        self.cursor_position += 1
    #@+node:ekr.20170510100003.1: *5* LeoMiniBuffer.h_return (executes command)
    def h_return (self, ch):
        '''
        Handle the return key in the minibuffer.
        Send the contents to k.masterKeyHandler.
        '''
        c = self.leo_c
        commandName = self.value.strip()
        self.value = ''
        self.update()
        c.k.masterCommand(
            commandName=commandName,
            event=KeyEvent(c,char='',event='',shortcut='',w=self),
            func=None,
            stroke=None,
        )
       
    #@+node:ekr.20170510094104.1: *5* LeoMiniBuffer.set_handlers
    def set_handlers(self):
        
        # pylint: disable=no-member
        # Override *all* other complex handlers.
        self.complex_handlers = [
            (curses.ascii.isprint, self.h_insert),
        ]
        self.handlers.update({
            # All other keys are passed on.
                # curses.ascii.TAB:    self.h_exit_down,
                # curses.KEY_BTAB:     self.h_exit_up,
            curses.ascii.NL:        self.h_return,
            curses.ascii.CR:        self.h_return,
            curses.KEY_HOME:        self.h_cursor_beginning,  # 262
            curses.KEY_END:         self.h_cursor_end,        # 358.
            curses.KEY_LEFT:        self.h_cursor_left,
            curses.KEY_RIGHT:       self.h_cursor_right,
            curses.ascii.BS:        self.h_delete_left,
            curses.KEY_BACKSPACE:   self.h_delete_left,
        })
    #@-others
#@+node:ekr.20170506035146.1: *3* class LeoMLTree (npyscreen.MLTree)
class LeoMLTree(npyscreen.MLTree):

    # pylint: disable=used-before-assignment
    _contained_widgets = LeoTreeLine
    continuation_line = "- more -" # value of contination line.
    
    # def __init__ (self, *args, **kwargs):
        # super(LeoMLTree, self).__init__(*args, **kwargs)
        
    # Note: The startup sequence sets leo_c and the value property/ivar.
           
    #@+others
    #@+node:ekr.20170510171826.1: *4* LeoMLTree.Entries
    #@+node:ekr.20170506044733.6: *5* LeoMLTree.delete_line
    def delete_line(self):

        trace = False
        trace_values = True
        node = self.values[self.cursor_line]
        assert isinstance(node, LeoTreeData), repr(node)
        if trace:
            g.trace('before', node.content)
            if trace_values: self.dump_values()
        if native:
            p = node.content
            assert p and isinstance(p, leoNodes.Position), repr(p)
            if p.hasParent() or p.hasNext() or p.hasBack():
                p.doDelete()
                self.values.clear_cache()
            else:
                g.trace('Can not delete the last top-level node')
                return
        else:
            parent = node.get_parent()
            grand_parent = parent and parent._parent
            if not grand_parent and len(parent._children) == 1:
                g.trace('Can not delete the last top-level node')
                return
            # Remove node and all its descendants.
            i = self.cursor_line
            nodes = [(i,node)]
            j = i + 1
            while j < len(self.values):
                node2 = self.values[j]
                if node.is_ancestor_of(node2):
                    nodes.append((j,node2),)
                    j += 1
                else:
                    break
            for j, node2 in reversed(nodes):
                del self.values[j]
            # Update the parent.
            parent._children = [z for z in parent._children if z != node]
        # Clearing these caches suffice to do a proper redraw
        self._last_values = None
        self._last_value = None
        if trace and trace_values:
            g.trace('after')
            self.dump_values()
        self.display()
            # This is widget.display:
                # (when not self.hidden)
                #self.update()
                    # LeoMLTree.update or MultiLine.update
                # self.parent.refresh()
                    # LeoForm.refresh
    #@+node:ekr.20170507171518.1: *5* LeoMLTree.dump_code/values/widgets
    def dump_code(self, code):
        d = {
            -2: 'left', -1: 'up', 1: 'down', 2: 'right',
            127: 'escape', 130: 'mouse',
        }
        return d.get(code) or 'unknown how_exited: %r' % code

    def dump_values(self):
        def info(z):
            return '%15s: %s' % (z._parent.get_content(), z.get_content())
        g.printList([info(z) for z in self.values])
        
    def dump_widgets(self):
        def info(z):
            return '%s.%s' % (id(z), z.__class__.__name__)
        g.printList([info(z) for z in self._my_widgets])
    #@+node:ekr.20170506044733.4: *5* LeoMLTree.edit_headline
    def edit_headline(self):

        trace = False
        assert self.values, g.callers()
        try:
            active_line = self._my_widgets[(self.cursor_line-self.start_display_at)]
            assert isinstance(active_line, LeoTreeLine)
            if trace: g.trace('LeoMLTree.active_line: %r' % active_line)
        except IndexError:
            # pylint: disable=pointless-statement
            self._my_widgets[0]
                # Does this have something to do with weakrefs?
            self.cursor_line = 0
            self.insert_line()
            return True
        active_line.highlight = False
        active_line.edit()
        if native:
            self.values.clear_cache()
        else:
            try:
                self.values[self.cursor_line] = active_line.value
            except IndexError:
                self.values.append(active_line.value)
                if not self.cursor_line:
                    self.cursor_line = 0
                self.cursor_line = len(self.values) - 1
        self.reset_display_cache()
        self.display()
        return True
    #@+node:ekr.20170523113530.1: *5* LeoMLTree.get_nth_visible_position
    def get_nth_visible_position(self, n):
        '''Return the n'th visible position.'''
        c = self.leo_c
        limit, junk = c.visLimit()
        p = limit.copy() if limit else c.rootPosition()
        i = 0
        while p:
            if i == n:
                return p
            else:
                p.moveToVisNext(c)
                i += 1
        g.trace('Can not happen', n)
        return None
    #@+node:ekr.20170514065422.1: *5* LeoMLTree.intraFileDrop
    def intraFileDrop(self, fn, p1, p2):
        pass
    #@+node:ekr.20170506044733.2: *5* LeoMLTree.new_mltree_node
    def new_mltree_node(self):
        '''
        Insert a new outline TreeData widget at the current line.
        As with Leo, insert as the first child of the current line if
        the current line is expanded. Otherwise insert after the current line.
        '''
        trace = False
        trace_values = True
        node = self.values[self.cursor_line]
        headline = 'New headline'
        if node.has_children() and node.expanded:
            node = node.new_child_at(index=0, content=headline)
        elif node.get_parent():
            parent = node.get_parent()
            node = parent.new_child(content=headline)
        else:
            parent = self.hidden_root_node
            index = parent._children.index(node)
            node = parent.new_child_at(index=index, content=headline)
        if trace:
            g.trace('LeoMLTree: line: %s %s' % (self.cursor_line, headline))
            if trace_values: self.dump_values()
        return node
    #@+node:ekr.20170506044733.5: *5* LeoMLTree.insert_line
    def insert_line(self):
        
        trace = False
        n = 0 if self.cursor_line is None else self.cursor_line
        if trace: g.trace('line: %r', n)
        if native:
            data = self.values[n] # data is a LeoTreeData
            p = data.content
            assert p and isinstance(p, leoNodes.Position)
            if p.hasChildren() and p.isExpanded():
                p2 = p.insertAsFirstChild()
            else:
                p2 = p.insertAfter()
            self.cursor_line += 1
            p2.h = 'New Headline'
            self.values.clear_cache()
        else:
            self.values.insert(n+1, self.new_mltree_node())
            self.cursor_line += 1
        self.display()
        self.edit_headline()
    #@+node:ekr.20170506045346.1: *4* LeoMLTree.Handlers
    # These insert or delete entire outline nodes.
    #@+node:ekr.20170523112839.1: *5* LeoMLTree.handle_mouse_event
    def handle_mouse_event(self, mouse_event):
        '''Called from InputHandler.h_exit_mouse.'''
        # From MultiLine...
        data = self.interpret_mouse_event(mouse_event)
        mouse_id, rel_x, rel_y, z, bstate = data
        self.cursor_line = (
            rel_y // 
            self._contained_widget_height + self.start_display_at
        )
        # Now, set the correct position.
        if native:
            c = self.leo_c
            p = self.get_nth_visible_position(self.cursor_line)
            c.frame.tree.select(p)
    #@+node:ekr.20170516055435.4: *5* LeoMLTree.h_collapse_all
    def h_collapse_all(self, ch):
        
        if native:
            c = self.leo_c
            for p in c.all_unique_positions():
                p.v.contract()
            self.values.clear_cache()
        else:
            for v in self._walk_tree(self._myFullValues, only_expanded=True):
                v.expanded = False
        self._cached_tree = None
        self.cursor_line = 0
        self.display()

    #@+node:ekr.20170516055435.2: *5* LeoMLTree.h_collapse_tree
    def h_collapse_tree(self, ch):

        node = self.values[self.cursor_line]
        if native:
            p = node.content
            assert p and isinstance(p, leoNodes.Position), repr(p)
            p.v.contract()
            self.values.clear_cache()
        else:
            if node.expanded and self._has_children(node):
                # Collapse the node.
                node.expanded = False
            elif 0: # Optional.
                # Collapse all the children.
                depth = self._find_depth(node) - 1
                cursor_line = self.cursor_line - 1
                while cursor_line >= 0:
                    if depth == self._find_depth(node):
                        self.cursor_line = cursor_line
                        node.expanded = False
                        break
                    else:
                        cursor_line -= 1
        self._cached_tree = None
            # Invalidate the display cache.
        self.display()
    #@+node:ekr.20170513091821.1: *5* LeoMLTree.h_cursor_line_down
    def h_cursor_line_down(self, ch):
        
        c = self.leo_c
        self.cursor_line = min(len(self.values)-1, self.cursor_line+1)
        if native:
            p = self.get_nth_visible_position(self.cursor_line)
            c.frame.tree.select(p)
    #@+node:ekr.20170513091928.1: *5* LeoMLTree.h_cursor_line_up
    def h_cursor_line_up(self, ch):
        
        c = self.leo_c
        self.cursor_line = max(0, self.cursor_line-1)
        if native:
            p = self.get_nth_visible_position(self.cursor_line)
            c.frame.tree.select(p)
    #@+node:ekr.20170506044733.12: *5* LeoMLTree.h_delete
    def h_delete(self, ch):

        c = self.leo_c
        self.delete_line()
        if native:
            p = self.get_nth_visible_position(self.cursor_line)
            c.frame.tree.select(p)
    #@+node:ekr.20170506044733.10: *5* LeoMLTree.h_edit_headline
    def h_edit_headline(self, ch):
        '''Called when the user types "h".'''
        self.edit_headline()
    #@+node:ekr.20170516055435.5: *5* LeoMLTree.h_expand_all
    def h_expand_all(self, ch):
        
        if native:
            c = self.leo_c
            for p in c.all_unique_positions():
                p.v.expand()
            self.values.clear_cache()
        else:
            for v in self._walk_tree(self._myFullValues, only_expanded=False):
                v.expanded    = True
        self._cached_tree = None
        self.cursor_line  = 0
        self.display()
    #@+node:ekr.20170516055435.3: *5* LeoMLTree.h_expand_tree
    def h_expand_tree(self, ch):

        node = self.values[self.cursor_line]
        if native:
            p = node.content
            assert p and isinstance(p, leoNodes.Position), repr(p)
            p.expand() # Don't use p.v.expand()
            self.values.clear_cache()
        else:
            # First, expand the node.
            if not node.expanded:
                node.expanded = True
            elif 0: # Optional.
                # Next, expand all children.
                for z in self._walk_tree(node, only_expanded=False):
                    z.expanded = True
        self._cached_tree = None
            # Invalidate the cache.
        self.display()
    #@+node:ekr.20170506044733.11: *5* LeoMLTree.h_insert
    def h_insert(self, ch):

        self.insert_line()
        if native:
            c = self.leo_c
            p = self.get_nth_visible_position(self.cursor_line)
            c.frame.tree.select(p)
    #@+node:ekr.20170506035413.1: *5* LeoMLTree.h_move_left
    def h_move_left(self, ch):
        
        node = self.values[self.cursor_line]
        if not node:
            g.trace('no node', self.cursor_line, repr(node))
            return
        if native:
            c = self.leo_c
            p = node.content
            assert p and isinstance(p, leoNodes.Position), repr(p)
            if p.hasChildren() and p.isExpanded():
                self.h_collapse_tree(ch)
                self.values.clear_cache()
            elif p.hasParent():
                parent = p.parent()
                parent.contract() # Don't use parent.v.contract.
                # Set the cursor to the parent's index.
                i = self.cursor_line - 1
                while i >= 0:
                    node2 = self.values[i]
                    if node2 is None:
                        g.trace('oops: no node2', i)
                        break
                    p2 = node2.content
                    if p2 == parent:
                        break
                    i -= 1
                self.cursor_line = max(0, i)
                self.values.clear_cache()
                c.frame.tree.select(p)
            else:
                pass # This is what Leo does.
        else:
            if self._has_children(node) and node.expanded:
                self.h_collapse_tree(ch)
            else:
                self.h_cursor_line_up(ch)
    #@+node:ekr.20170506035419.1: *5* LeoMLTree.h_move_right
    def h_move_right(self, ch):

        node = self.values[self.cursor_line]
        if not node:
            g.trace('no node')
            return
        if native:
            p = node.content
            assert p and isinstance(p, leoNodes.Position), repr(p)
            if p.hasChildren():
                if p.isExpanded():
                    self.h_cursor_line_down(ch)
                else:
                    self.h_expand_tree(ch)
            else:
                pass # This is what Leo does.
        else:
            if self._has_children(node):
                if node.expanded:
                    self.h_cursor_line_down(ch)
                else:
                    self.h_expand_tree(ch)
            else:
                self.h_cursor_line_down(ch)
    #@+node:ekr.20170507175304.1: *5* LeoMLTree.set_handlers
    def set_handlers(self):
        
        # pylint: disable=no-member
        d = {
            curses.KEY_LEFT: self.h_move_left,
            curses.KEY_RIGHT: self.h_move_right,
            ord('d'): self.h_delete,
            ord('h'): self.h_edit_headline,
            ord('i'): self.h_insert,
            # curses.ascii.CR:        self.h_edit_cursor_line_value,
            # curses.ascii.NL:        self.h_edit_cursor_line_value,
            # curses.ascii.SP:        self.h_edit_cursor_line_value,
            # curses.ascii.DEL:       self.h_delete_line_value,
            # curses.ascii.BS:        self.h_delete_line_value,
            # curses.KEY_BACKSPACE:   self.h_delete_line_value,
        }
        self.handlers.update(d)
    #@+node:ekr.20170516100256.1: *5* LeoMLTree.set_up_handlers
    def set_up_handlers(self):
        super(LeoMLTree, self).set_up_handlers()
        assert not hasattr(self, 'hidden_root_node'), repr(self)
        self.leo_c = None # Set later.
        self.currentItem = None
            # Used by CoreTree class.
        self.hidden_root_node = None
        self.set_handlers()

    #@+node:ekr.20170516055435.6: *5* LeoMLTree.set_up_handlers (REF)
    # def set_up_handlers(self):
        # '''TreeLineAnnotated.set_up_handlers.'''
        # super(MLTree, self).set_up_handlers()
        # self.handlers.update({
            # ord('<'): self.h_collapse_tree,
            # ord('>'): self.h_expand_tree,
            # ord('['): self.h_collapse_tree,
            # ord(']'): self.h_expand_tree,
            # ord('{'): self.h_collapse_all,
            # ord('}'): self.h_expand_all,
            # ord('h'): self.h_collapse_tree,
            # ord('l'): self.h_expand_tree,          
        # })
    #@+node:ekr.20170513032502.1: *4* LeoMLTree.update & helpers
    def update(self, clear=True):
        '''Redraw the tree.'''
        # This is a major refactoring of MultiLine.update.
        if self.editing:
            self._init_update()
        if self._must_redraw(clear):
            self._redraw(clear)
        # Remember the previous values.
        self._last_start_display_at = self.start_display_at
        self._last_cursor_line = self.cursor_line
        if native:
            pass
        else:
            self._last_values = copy.copy(self.values)
            self._last_value = copy.copy(self.value)
    #@+node:ekr.20170513122253.1: *5* LeoMLTree._init_update
    def _init_update(self):
        '''Put self.cursor_line and self.start_display_at in range.'''
        # pylint: disable=access-member-before-definition
        display_length = len(self._my_widgets)
        self.cursor_line = max(0, min(len(self.values)-1, self.cursor_line))
        if self.slow_scroll:
            # Scroll by lines.
            if self.cursor_line > self.start_display_at + display_length - 1:
                self.start_display_at = self.cursor_line - (display_length - 1)
            if self.cursor_line < self.start_display_at:
                self.start_display_at = self.cursor_line
        else:
            # Scroll by pages.
            if self.cursor_line > self.start_display_at + (display_length - 2):
                self.start_display_at = self.cursor_line
            if self.cursor_line < self.start_display_at:
                self.start_display_at = self.cursor_line - (display_length - 2)
                if self.start_display_at < 0: self.start_display_at = 0
    #@+node:ekr.20170513123010.1: *5* LeoMLTree._must_redraw
    def _must_redraw(self, clear):
        '''Return a list of reasons why we must redraw.'''
        trace = False
        table = (
            ('cache', not self._safe_to_display_cache or self.never_cache),
            ('value', self._last_value is not self.value),
            ('values', self.values != self._last_values),
            ('start', self.start_display_at != self._last_start_display_at),
            ('clear', clear != True),
            ('cursor', self._last_cursor_line != self.cursor_line),
            ('filter', self._last_filter != self._filter),
            ('editing', not self.editing),
        )
        reasons = (reason for (reason, cond) in table if cond)
        if trace: g.trace('line: %2s %-20s %s' % (
            self.cursor_line,
            ','.join(reasons),
            self.values[self.cursor_line].content))
        return reasons
    #@+node:ekr.20170513122427.1: *5* LeoMLTree._redraw & helpers
    def _redraw(self, clear):
        '''Do the actual redraw.'''
        # self.clear is Widget.clear. It does *not* use _myWidgets.
        if (clear is True or
            clear is None and self._last_start_display_at != self.start_display_at
        ):
            self.clear()
        self._last_start_display_at = start = self.start_display_at
        i = self.start_display_at
        for line in self._my_widgets[:-1]:
            assert isinstance(line, LeoTreeLine), repr(line)
            self._print_line(line, i)
            line.update(clear=True)
            i += 1
        # Do the last line
        line = self._my_widgets[-1]
        if (len(self.values) <= i + 1):
            self._print_line(line, i)
            line.update(clear=False)
        elif len((self._my_widgets) * self._contained_widget_height) < self.height:
            self._print_line(line, i)
            line.update(clear=False)
            self._put_continuation_line()
        else:
            line.clear() # This is Widget.clear.
            self._put_continuation_line()
        # Assert that print_line leaves start_display_at unchanged.
        assert start == self.start_display_at, (start, self.start_display_at)
        # Finish
        if self.editing:
            line = self._my_widgets[(self.cursor_line - start)]
            line.highlight = True
            line.update(clear=True)
    #@+node:ekr.20170513032717.1: *6* LeoMLTree._print_line
    def _print_line(self, line, i):

        #
        # if self.widgets_inherit_color and self.do_colors():
            # line.color = self.color
        
        self._set_line_values(line, i)
            # Sets line.value
        if line.value is not None:
            assert isinstance(line.value, LeoTreeData), repr(line.value)
        self._set_line_highlighting(line, i)
    #@+node:ekr.20170513102428.1: *6* LeoMLTree._put_continuation_line
    def _put_continuation_line(self):
        '''Print the line indicating there are more lines left.'''
        s = self.continuation_line
        x = self.relx
        y = self.rely + self.height - 1
        if self.do_colors():
            style = self.parent.theme_manager.findPair(self, 'CONTROL')
            self.parent.curses_pad.addstr(y, x, s, style)
        else:
            self.parent.curses_pad.addstr(y, x, s)
    #@+node:ekr.20170513075423.1: *6* LeoMLTree._set_line_values
    def _set_line_values(self, line, i):
        '''Set internal values of line using self.values[i] and self.values[i+1]'''
        trace = False
        trace_ok = True
        trace_empty = True
        line.leo_c = self.leo_c
            # Inject the ivar.
        values = self.values
        n = len(values)
        val = values[i] if 0 <= i < n else None
        if not val:
            line._tree_depth        = False
            line._tree_depth_next   = False
            line._tree_expanded     = False
            line._tree_has_children = False
            line._tree_ignore_root  = None
            line._tree_last_line    = True #
            line._tree_real_value   = None
            line._tree_sibling_next = False
            line.value = None
            if trace and trace_empty: g.trace(i, n, '<empty>', repr(val))
            return
        assert isinstance(val, LeoTreeData), repr(val)
        # Aliases
        val1 = values[i+1] if i+1 < n else None
        val1_depth = val1.find_depth() if val1 else False
        # Common settings.
        line._tree_depth = val.find_depth()
        line._tree_depth_next = val1_depth
        line._tree_ignore_root = self._get_ignore_root(self._myFullValues)
        line._tree_sibling_next = line._tree_depth == val1_depth
        line._tree_real_value = val
        line.value = val
        if native:
            p = val.content
            assert p and isinstance(p, leoNodes.Position), repr(p)
            line._tree_expanded = p.isExpanded()
            line._tree_has_children = p.hasChildren()
            line._tree_last_line = not p.hasNext()
        else:
            line._tree_expanded = val.expanded
            line._tree_has_children = bool(val._children)
            line._tree_last_line = not bool(line._tree_sibling_next)
        if trace and trace_ok:
            content = line.value.content
            s = content.h if native else content
            g.trace(i, n, s)
    #@+node:ekr.20170516101203.1: *4* LeoMLTree.values
    if native:
        _myFullValues = LeoTreeData()
        values = None
    else:
        # This property converts the (possibly cached) result of converting
        # the root node (_myFullValues) and its *visible* decendants to a list.
        # To invalidate the cache, set __cached_tree = None
        #@+others
        #@+node:ekr.20170517142822.1: *5* _getValues
        def _getValues(self):
            '''
            Return the (possibly cached) list returned by self._myFullValues.get_tree_as_list().

            Setting _cached_tree to None invalidates the cache.
            '''
            # pylint: disable=access-member-before-definition
            if getattr(self, '_cached_tree', None):
                return self._cached_tree_as_list
            else:
                self._cached_tree = self._myFullValues
                self._cached_tree_as_list = self._myFullValues.get_tree_as_list()
                return self._cached_tree_as_list

        #@+node:ekr.20170518054457.1: *5* _setValues
        def _setValues(self, tree):
            self._myFullValues = tree or LeoTreeData()
        #@-others
        values = property(_getValues, _setValues)
    #@-others
#@+node:ekr.20170517072429.1: *3* class LeoValues (npyscreen.TreeData)
class LeoValues(npyscreen.TreeData):
    '''
    A class to replace the MLTree.values property.
    This is formally an subclass of TreeData.
    '''
    
    def __init__(self, c, tree):
        '''Ctor for LeoValues class.'''
        super(LeoValues, self).__init__()
            # Init the base class.
        self.c = c
            # The commander of this outline.
        self.data_cache = {}
            # Keys are ints, values are LeoTreeData objects.
        self.position_cache = {}
            # Keys are ints, values are copies of posiitions.
        self.tree = tree
            # A LeoMLTree.

    #@+others
    #@+node:ekr.20170517090738.1: *4* values.__getitem__ and get_data
    def __getitem__(self, n):
        '''Called from LeoMLTree._setLineValues.'''
        return self.get_data(n)

    def get_data(self, n):
        '''Return a LeoTreeData for the n'th visible position of the outline.'''
        trace = False
        c = self.c
        # Look for n or n-1 in the caches.
        data = self.data_cache.get(n)
        if data:
            if trace: g.trace('cached', n, repr(data))
            return data
        p = self.position_cache.get(max(0,n-1))
        if p:
            p = p.copy()
                # Never change the cached position!
                # LeoTreeData(p) makes a copy of p.
            p = p.moveToVisNext(c)
            if p:
                self.position_cache[n] = p
                self.data_cache[n] = data = LeoTreeData(p)
                if trace: g.trace(' after', n, repr(data))
                return data
            else:
                if trace: g.trace(' fail1', n, repr(data))
                return None
        # Search the tree, caching the result.
        i, p = 0, c.rootPosition()
        while p:
            if i == n:
                self.position_cache[n] = p
                self.data_cache[n] = data = LeoTreeData(p)
                if trace: g.trace(' found', n, repr(data))
                return data
            else:
                p.moveToVisNext(c)
                i += 1
        if trace: g.trace(' fail2', n, repr(data))
        return None
    #@+node:ekr.20170518060014.1: *4* values.__len__
    def __len__(self):
        '''
        Return the putative length of the values array,
        that is, the number of visible nodes in the outline.
        '''
        c = self.c
        n, p = 0, c.rootPosition()
        while p:
            n += 1
            p.moveToVisNext(c)
        # g.trace(n)
        return n
    #@+node:ekr.20170519041459.1: *4* values.clear_cache
    def clear_cache(self):
        
        self.data_cache = {}
        self.position_cache = {}
    #@-others
#@+node:ekr.20170522081122.1: ** Wrapper classes
#@+others
#@+node:ekr.20170511053143.1: *3*  class TextMixin (object)
class TextMixin(object):
    '''A minimal mixin class for QTextEditWrapper and QScintillaWrapper classes.'''
    #@+others
    #@+node:ekr.20170511053143.2: *4* tm.ctor & helper
    def __init__(self, c=None):
        '''Ctor for TextMixin class'''
        self.c = c
        self.changingText = False
            # A lockout for onTextChanged.
        self.enabled = True
        self.supportsHighLevelInterface = True
            # A flag for k.masterKeyHandler and isTextWrapper.
        self.tags = {}
        self.configDict = {}
            # Keys are tags, values are colors (names or values).
        self.configUnderlineDict = {}
            # Keys are tags, values are True
        self.virtualInsertPoint = None
        if c:
            self.injectIvars(c)
    #@+node:ekr.20170511053143.3: *5* tm.injectIvars
    def injectIvars(self, name='1', parentFrame=None):
        '''Inject standard leo ivars into the QTextEdit or QsciScintilla widget.'''
        p = self.c.currentPosition()
        if name == '1':
            self.leo_p = None # Will be set when the second editor is created.
        else:
            self.leo_p = p and p.copy()
        self.leo_active = True
        # Inject the scrollbar items into the text widget.
        self.leo_bodyBar = None
        self.leo_bodyXBar = None
        self.leo_chapter = None
        self.leo_frame = None
        self.leo_name = name
        self.leo_label = None
        return self
    #@+node:ekr.20170511053143.4: *4* tm.getName
    def getName(self):
        return self.name # Essential.
    #@+node:ekr.20170511053143.8: *4* tm.Generic high-level interface
    # These call only wrapper methods.
    #@+node:ekr.20170511053143.13: *5* tm.appendText
    def appendText(self, s):
        '''TextMixin'''
        s2 = self.getAllText()
        self.setAllText(s2 + s)
        self.setInsertPoint(len(s2))
    #@+node:ekr.20170511053143.10: *5* tm.clipboard_clear/append
    def clipboard_append(self, s):
        s1 = g.app.gui.getTextFromClipboard()
        g.app.gui.replaceClipboardWith(s1 + s)

    def clipboard_clear(self):
        g.app.gui.replaceClipboardWith('')
    #@+node:ekr.20170511053143.14: *5* tm.delete
    def delete(self, i, j=None):
        '''TextMixin'''
        i = self.toPythonIndex(i)
        if j is None: j = i + 1
        j = self.toPythonIndex(j)
        # This allows subclasses to use this base class method.
        if i > j: i, j = j, i
        s = self.getAllText()
        self.setAllText(s[: i] + s[j:])
        # Bug fix: Significant in external tests.
        self.setSelectionRange(i, i, insert=i)
    #@+node:ekr.20170511053143.15: *5* tm.deleteTextSelection
    def deleteTextSelection(self):
        '''TextMixin'''
        i, j = self.getSelectionRange()
        self.delete(i, j)
    #@+node:ekr.20170511053143.9: *5* tm.Enable/disable
    def disable(self):
        self.enabled = False

    def enable(self, enabled=True):
        self.enabled = enabled
    #@+node:ekr.20170511053143.16: *5* tm.get
    def get(self, i, j=None):
        '''TextMixin'''
        # 2012/04/12: fix the following two bugs by using the vanilla code:
        # https://bugs.launchpad.net/leo-editor/+bug/979142
        # https://bugs.launchpad.net/leo-editor/+bug/971166
        s = self.getAllText()
        i = self.toPythonIndex(i)
        j = self.toPythonIndex(j)
        return s[i: j]
    #@+node:ekr.20170511053143.17: *5* tm.getLastPosition & getLength
    def getLastPosition(self, s=None):
        '''TextMixin'''
        return len(self.getAllText()) if s is None else len(s)

    def getLength(self, s=None):
        '''TextMixin'''
        return len(self.getAllText()) if s is None else len(s)
    #@+node:ekr.20170511053143.18: *5* tm.getSelectedText
    def getSelectedText(self):
        '''TextMixin'''
        i, j = self.getSelectionRange()
        if i == j:
            return ''
        else:
            s = self.getAllText()
            return s[i: j]
    #@+node:ekr.20170511053143.19: *5* tm.insert
    def insert(self, i, s):
        '''TextMixin'''
        s2 = self.getAllText()
        i = self.toPythonIndex(i)
        self.setAllText(s2[: i] + s + s2[i:])
        self.setInsertPoint(i + len(s))
        return i
    #@+node:ekr.20170511053143.24: *5* tm.rememberSelectionAndScroll
    def rememberSelectionAndScroll(self):
        trace = (False or g.trace_scroll) and not g.unitTesting
        v = self.c.p.v # Always accurate.
        v.insertSpot = self.getInsertPoint()
        i, j = self.getSelectionRange()
        if i > j: i, j = j, i
        assert(i <= j)
        v.selectionStart = i
        v.selectionLength = j - i
        v.scrollBarSpot = spot = self.getYScrollPosition()
        if trace:
            g.trace(spot, v.h)
            # g.trace(id(v),id(self),i,j,ins,spot,v.h)
    #@+node:ekr.20170511053143.20: *5* tm.seeInsertPoint
    def seeInsertPoint(self):
        '''Ensure the insert point is visible.'''
        self.see(self.getInsertPoint())
            # getInsertPoint defined in client classes.
    #@+node:ekr.20170511053143.21: *5* tm.selectAllText
    def selectAllText(self, s=None):
        '''TextMixin.'''
        self.setSelectionRange(0, self.getLength(s))
    #@+node:ekr.20170511053143.11: *5* tm.setFocus
    def setFocus(self):
        '''TextMixin.setFocus'''
        g.app.gui.set_focus(self)
        
    #@+node:ekr.20170511053143.25: *5* tm.tag_configure
    def tag_configure(self, *args, **keys):

        trace = False and not g.unitTesting
        if trace: g.trace(args, keys)
        if len(args) == 1:
            key = args[0]
            self.tags[key] = keys
            val = keys.get('foreground')
            underline = keys.get('underline')
            if val:
                self.configDict[key] = val
            if underline:
                self.configUnderlineDict[key] = True
        else:
            g.trace('oops', args, keys)

    tag_config = tag_configure
    #@+node:ekr.20170511053143.22: *5* tm.toPythonIndex
    def toPythonIndex(self, index, s=None):
        '''TextMixin'''
        if s is None:
            s = self.getAllText()
        i = g.toPythonIndex(s, index)
        # g.trace(index,len(s),i,s[i:i+10])
        return i
    #@+node:ekr.20170511053143.23: *5* tm.toPythonIndexRowCol
    def toPythonIndexRowCol(self, index):
        '''TextMixin'''
        s = self.getAllText()
        i = self.toPythonIndex(index)
        row, col = g.convertPythonIndexToRowCol(s, i)
        return i, row, col
    #@-others
#@+node:ekr.20170504034655.1: *3* class BodyWrapper (leoFrame.StringTextWrapper)
class BodyWrapper(leoFrame.StringTextWrapper):
    '''
    A Wrapper class for Leo's body.
    This is c.frame.body.wrapper.
    '''
    
    def __init__(self, c, name, w):
        '''Ctor for BodyWrapper class'''
        leoFrame.StringTextWrapper.__init__(self, c, name)
        self.changingText = False
            # A lockout for onTextChanged.
        self.widget = w
        self.injectIvars(c)
            # These are used by Leo's core.

    #@+others
    #@+node:ekr.20170504034655.3: *4* bw.injectIvars
    def injectIvars(self, name='1', parentFrame=None):
        '''Inject standard leo ivars into the QTextEdit or QsciScintilla widget.'''
        p = self.c.currentPosition()
        if name == '1':
            self.leo_p = None # Will be set when the second editor is created.
        else:
            self.leo_p = p and p.copy()
        self.leo_active = True
        # Inject the scrollbar items into the text widget.
        self.leo_bodyBar = None
        self.leo_bodyXBar = None
        self.leo_chapter = None
        self.leo_frame = None
        self.leo_name = name
        self.leo_label = None
    #@+node:ekr.20170504034655.6: *4* bw.onCursorPositionChanged (called?)
    def onCursorPositionChanged(self, event=None):
        
        g.trace('=====')
        
        # c = self.c
        # name = c.widget_name(self)
        # # Apparently, this does not cause problems
        # # because it generates no events in the body pane.
        # if name.startswith('body'):
            # if hasattr(c.frame, 'statusLine'):
                # c.frame.statusLine.update()
    #@+node:ekr.20170504034655.7: *4* bw.onTextChanged (not called yet)
    def onTextChanged(self):
        '''
        Update Leo after the body has been changed.

        self.selecting is guaranteed to be True during
        the entire selection process.
        '''
        g.trace('**********', g.callers())
        ###
            # # Important: usually w.changingText is True.
            # # This method very seldom does anything.
            # trace = False and not g.unitTesting
            # verbose = False
            # c = self.c; p = c.p
            # tree = c.frame.tree
            # if self.changingText:
                # if trace and verbose: g.trace('already changing')
                # return
            # if tree.tree_select_lockout:
                # if trace and verbose: g.trace('selecting lockout')
                # return
            # if tree.selecting:
                # if trace and verbose: g.trace('selecting')
                # return
            # if tree.redrawing:
                # if trace and verbose: g.trace('redrawing')
                # return
            # if not p:
                # if trace: g.trace('*** no p')
                # return
            # newInsert = self.getInsertPoint()
            # newSel = self.getSelectionRange()
            # newText = self.getAllText() # Converts to unicode.
            # # Get the previous values from the VNode.
            # oldText = p.b
            # if oldText == newText:
                # # This can happen as the result of undo.
                # return
            # i, j = p.v.selectionStart, p.v.selectionLength
            # oldSel = (i, i + j)
            # if trace: g.trace('oldSel', oldSel, 'newSel', newSel)
            # oldYview = None
            # undoType = 'Typing'
            # c.undoer.setUndoTypingParams(p, undoType,
                # oldText=oldText, newText=newText,
                # oldSel=oldSel, newSel=newSel, oldYview=oldYview)
            # # Update the VNode.
            # p.v.setBodyString(newText)
            # if True:
                # p.v.insertSpot = newInsert
                # i, j = newSel
                # i, j = self.toPythonIndex(i), self.toPythonIndex(j)
                # if i > j: i, j = j, i
                # p.v.selectionStart, p.v.selectionLength = (i, j - i)
            # # No need to redraw the screen.
            # c.recolor()
            # if g.app.qt_use_tabs:
                # if trace: g.trace(c.frame.top)
            # if not c.changed and c.frame.initComplete:
                # c.setChanged(True)
            # c.frame.body.updateEditors()
            # c.frame.tree.updateIcon(p)
    #@+node:ekr.20170511053143.7: *4* tm.onTextChanged (REF)
    # def onTextChanged(self):
        # '''
        # Update Leo after the body has been changed.

        # self.selecting is guaranteed to be True during
        # the entire selection process.
        # '''
        # # Important: usually self.changingText is True.
        # # This method very seldom does anything.
        # trace = True and not g.unitTesting
        # verbose = True
        # c, p = self.c, self.c.p
        # tree = c.frame.tree
        # if self.changingText:
            # if trace and verbose: g.trace('already changing')
            # return
        # if tree.tree_select_lockout:
            # if trace and verbose: g.trace('selecting lockout')
            # return
        # if tree.selecting:
            # if trace and verbose: g.trace('selecting')
            # return
        # if tree.redrawing:
            # if trace and verbose: g.trace('redrawing')
            # return
        # if not p:
            # if trace: g.trace('*** no p')
            # return
        # newInsert = self.getInsertPoint()
        # newSel = self.getSelectionRange()
        # newText = self.getAllText() # Converts to unicode.
        # # Get the previous values from the VNode.
        # oldText = p.b
        # if oldText == newText:
            # # This can happen as the result of undo.
            # # g.error('*** unexpected non-change')
            # return
        # # g.trace('**',len(newText),p.h,'\n',g.callers(8))
        # # oldIns  = p.v.insertSpot
        # i, j = p.v.selectionStart, p.v.selectionLength
        # oldSel = (i, i + j)
        # if trace: g.trace('oldSel', oldSel, 'newSel', newSel)
        # oldYview = None
        # undoType = 'Typing'
        # c.undoer.setUndoTypingParams(p, undoType,
            # oldText=oldText, newText=newText,
            # oldSel=oldSel, newSel=newSel, oldYview=oldYview)
        # # Update the VNode.
        # p.v.setBodyString(newText)
        # if True:
            # p.v.insertSpot = newInsert
            # i, j = newSel
            # i, j = self.toPythonIndex(i), self.toPythonIndex(j)
            # if i > j: i, j = j, i
            # p.v.selectionStart, p.v.selectionLength = (i, j - i)
        # # No need to redraw the screen.
        # c.recolor()
        # if g.app.qt_use_tabs:
            # if trace: g.trace(c.frame.top)
        # if not c.changed and c.frame.initComplete:
            # c.setChanged(True)
        # c.frame.body.updateEditors()
        # c.frame.tree.updateIcon(p)
    #@-others
#@+node:ekr.20170522002403.1: *3* class HeadWrapper (leoFrame.StringTextWrapper)
class HeadWrapper(leoFrame.StringTextWrapper):
    '''
    A Wrapper class for headline widgets, returned by c.edit_widget(p)
    '''
    
    def __init__(self, c, name, p):
        '''Ctor for HeadWrapper class'''
        # g.trace('HeadWrapper', p.h)
        leoFrame.StringTextWrapper.__init__(self, c, name)
        self.trace = False # For tracing in base class.
        self.p = p.copy()
        self.s = p.v._headString

    #@+others
    #@+node:ekr.20170522014009.1: *4* hw.setAllText
    def setAllText(self, s):
        '''HeadWrapper.setAllText'''
        # Don't allow newlines.
        self.s = s.replace('\n','').replace('\r','')
        i = len(self.s)
        self.ins = i
        self.sel = i, i
        self.p.v._headString = self.s
    #@-others
#@+node:ekr.20170525062512.1: *3* class LogWrapper (leoFrame.StringTextWrapper)
class LogWrapper(leoFrame.StringTextWrapper):
    '''A Wrapper class for the log pane.'''
    
    def __init__(self, c, name, w):
        '''Ctor for LogWrapper class'''
        leoFrame.StringTextWrapper.__init__(self, c, name)
        self.trace = False # For tracing in base class.
        self.widget = w

    #@+others
    #@-others
#@+node:ekr.20170525105707.1: *3* class MiniBufferWrapper (leoFrame.StringTextWrapper)
class MiniBufferWrapper(leoFrame.StringTextWrapper):
    '''A Wrapper class for the minibuffer.'''
    
    def __init__(self, c, name, w):
        '''Ctor for MiniBufferWrapper class'''
        leoFrame.StringTextWrapper.__init__(self, c, name)
        self.trace = False # For tracing in base class.
        self.widget = w

    #@+others
    #@-others
#@-others
#@-others
#@@language python
#@@tabwidth -4
#@-leo
