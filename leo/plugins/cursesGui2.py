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
# import weakref
import leo.core.leoGlobals as g
import leo.core.leoFrame as leoFrame
import leo.core.leoGui as leoGui
import leo.core.leoMenu as leoMenu
import leo.core.leoNodes as leoNodes
import leo.core.leoPlugins as leoPlugins
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
native = True # True: use LeoValues object to return TreeData.
#@+<< forward reference classes >>
#@+node:ekr.20170511053555.1: **  << forward reference classes >>
#@+others
#@+node:ekr.20170508085942.1: *3*  class LeoTreeLine (npyscreen.TreeLine)
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
    #@+node:ekr.20170514104550.1: *4* LeoTreeLine._get_string_to_print (from TextfieldBase) 
    def _get_string_to_print(self):
        
        if native:
            # g.trace('LeoTreeLine: value:', repr(self.value))
            if self.value:
                assert isinstance(self.value, LeoTreeData)
                p = self.value.content
                assert isinstance(p, leoNodes.Position)
                assert p, g.callers()
                return p.h
            else:
                return ''
        else:
            s = self.value.content if self.value else None
        # g.trace(repr(s))
        return g.toUnicode(s) if s else None
    #@+node:ekr.20170514183049.1: *4* LeoTreeLine.display_value
    def display_value(self, vl):
        
        # vl is a weakref proxy to a LeoTreeData.
        if native:
            p = vl.content
            assert isinstance(p, leoNodes.Position)
            assert p, g.callers()
            return p.h
            # return vl.content.h if vl else ''
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
            ### This is Widget.when_check_value_changed.
            # try:
                # if self.value == self._old_value:
                    # return False
            # except AttributeError:
                # self._old_value = copy.deepcopy(self.value)
                # self.when_value_edited()
            # # Value must have changed:
            # self._old_value = copy.deepcopy(self.value)
            # self._internal_when_value_edited()
            # self.when_value_edited()
            # if hasattr(self, 'parent_widget'):
                # self.parent_widget.when_value_edited()
                # self.parent_widget._internal_when_value_edited()
            # return True
    #@+node:ekr.20170519024639.1: *4* LeoTreeLine.set_leo_headline (not used)
    # if native:
        
        # def set_leo_headline(self, data):
            
            # assert isinstance(self.value, LeoTreeData)
            # assert isinstance(data, LeoTreeData)
            # p = data.content
            # assert p and isinstance(p, leoNodes.Position), repr(p)
            # # g.trace('self.value.content', self.value.content)
            # # g.trace('      data.content', data.content)

    #@+node:ekr.20170514103905.1: *4* LeoTreeLine.XXX_print (from TreeLine and TextFieldBase)
    def XXX_print(self, left_margin=0):
        # pylint: disable=no-member
        #
        ###
        ### From TreeLine._print
        ###
        self.left_margin = left_margin
        self.parent.curses_pad.bkgdset(' ',curses.A_NORMAL)
        self.left_margin += self._print_tree(self.relx)
        if self.highlight:
            self.parent.curses_pad.bkgdset(' ',curses.A_STANDOUT)
        ###
        ### From TextFieldBase._print
        ###
        s = self.value and self.value.content
            ### LeoTreeLine.display_value and LeoTreeLine._get_string_to_print do this,
            ### So there is no need to override this method!!
        if not s:
            return
        s = g.toUnicode(s)
        column, i = 0, 0
        assert not self.syntax_highlighting
        if self.syntax_highlighting:
            self.update_highlighting(
                start=self.begin_at,
                end=self.maximum_string_length+self.begin_at-self.left_margin,
            )
            while column <= (self.maximum_string_length - self.left_margin):
                if not s or i > len(s)-1:
                    break
                if column > self.maximum_string_length:
                    break 
                try:
                    highlight = self._highlightingdata[self.begin_at+i]
                except Exception:
                    highlight = curses.A_NORMAL                
                self.parent.curses_pad.addstr(
                    self.rely,
                    self.relx+column+self.left_margin, 
                    self._print_unicode_char(s[i]), 
                    highlight
                )
                column += self.find_width_of_char(s[i])
                i += 1
        else: # No syntax highlighting.
            if self.do_colors(): # do_colors is a Widget member.
                findPair = self.parent.theme_manager.findPair
                if self.show_bold and self.color == 'DEFAULT':
                    color = findPair(self, 'BOLD') | curses.A_BOLD
                elif self.show_bold:
                    color = findPair(self, self.color) | curses.A_BOLD
                elif self.important:
                    color = findPair(self, 'IMPORTANT') | curses.A_BOLD
                else:
                    color = findPair(self)
            else:
                bold = self.important or self.show_bold
                color = curses.A_BOLD if bold else curses.A_NORMAL
            while column <= self.maximum_string_length - self.left_margin:
                if i > len(s)-1:
                    if self.highlight_whole_widget:
                        self.parent.curses_pad.addstr(
                            self.rely,
                            self.relx+column+self.left_margin, 
                            ' ', 
                            color,
                        )
                        column += 1
                        i += 1
                        continue
                    else:
                        break
                if column > self.maximum_string_length:
                    break 
                self.parent.curses_pad.addstr(
                    self.rely,
                    self.relx+column+self.left_margin, 
                    self._print_unicode_char(s[i]), 
                    color,
                )
                column += 1
                i += 1
    #@+node:ekr.20170514103557.1: *4* LeoTreeLine.XXX_update (from TreeLine, Inherits from textFieldBase)
    def XXX_update(self, clear=True, cursor=True):
        """Update the contents of the textbox, without calling the final refresh to the screen"""
        # pylint: disable=arguments-differ,no-member
        trace = False
        if trace:
            g.trace('LeoTree: cursor_position: %5r %s' % (
                self.cursor_position, self.value.content if self.value else 'None'))
        if clear: self.clear()
        if self.hidden:
            return True
        findPair = self.parent.theme_manager.findPair
        val = self.value.content if self.value else g.u('') 
            ### We **can** use MultiLine.update. (There is no TreeLine.update).
            ### This is the code in MultiLine.update.
                # val = self.values[self.cursor_line]
                # if isinstance(val, npysTree.TreeData):
                    # val = val.get_content()
            ### LeoTreeData.get_content just returns self.content,
            ### So that is good enough!
        val = g.toUnicode(val)
        self.begin_at = max(0, self.begin_at)
        if self.left_margin >= self.maximum_string_length:
            raise ValueError
        highlight_color = findPair(self, self.highlight_color)
        if self.editing:
            if cursor:
                if self.cursor_position is False:
                    self.cursor_position = len(val)
                else:
                    self.cursor_position = max(0, min(len(val), self.cursor_position))
                #
                if self.cursor_position < self.begin_at:
                    self.begin_at = self.cursor_position
                while self.cursor_position > self.begin_at + self.maximum_string_length - self.left_margin: # -1:
                    self.begin_at += 1
            else:
                if self.do_colors():
                    highlight_color = findPair(self, self.highlight_color)
                    self.parent.curses_pad.bkgdset(' ', highlight_color | curses.A_STANDOUT)
                else:
                    self.parent.curses_pad.bkgdset(' ', curses.A_STANDOUT)
        # Do this twice so that the _print method can ignore it if needed.
        if self.highlight:
            if self.do_colors():
                attributes = highlight_color
                if self.invert_highlight_color:
                    attributes |= curses.A_STANDOUT
                self.parent.curses_pad.bkgdset(' ', attributes)
            else:
                self.parent.curses_pad.bkgdset(' ',curses.A_STANDOUT)
        if self.show_bold:
            self.parent.curses_pad.attron(curses.A_BOLD)
        if self.important and not self.do_colors():
            self.parent.curses_pad.attron(curses.A_UNDERLINE)
        self._print()
        # reset everything to normal
        self.parent.curses_pad.attroff(curses.A_BOLD)
        self.parent.curses_pad.attroff(curses.A_UNDERLINE)
        self.parent.curses_pad.bkgdset(' ',curses.A_NORMAL)
        self.parent.curses_pad.attrset(0)
        if self.editing and cursor:
            self.print_cursor()
                # Call base-class method.
    #@-others
#@+node:ekr.20170511053143.1: *3*  class CursesTextMixin (object)
class CursesTextMixin(object):
    '''A minimal mixin class for QTextEditWrapper and QScintillaWrapper classes.'''
    #@+others
    #@+node:ekr.20170511053143.2: *4* ctm.ctor & helper
    def __init__(self, c=None):
        '''Ctor for CursesTextMixin class'''
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
    #@+node:ekr.20170511053143.3: *5* ctm.injectIvars
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
    #@+node:ekr.20170511053143.4: *4* ctm.getName
    def getName(self):
        return self.name # Essential.
    #@+node:ekr.20170511053143.5: *4* ctm.Event handlers (revise or remove)
    # These are independent of the kind of widget.
    #@+node:ekr.20170511053143.6: *5* ctm.onCursorPositionChanged
    def onCursorPositionChanged(self, event=None):
        '''CursesTextMixin'''
        g.trace('=====', g.callers())
        ###
            # c = self.c
            # name = c.widget_name(self)
            # # Apparently, this does not cause problems
            # # because it generates no events in the body pane.
            # if name.startswith('body'):
                # if hasattr(c.frame, 'statusLine'):
                    # c.frame.statusLine.update()
    #@+node:ekr.20170511053143.7: *5* ctm.onTextChanged
    def onTextChanged(self):
        '''
        Update Leo after the body has been changed.

        self.selecting is guaranteed to be True during
        the entire selection process.
        '''
        # Important: usually self.changingText is True.
        # This method very seldom does anything.
        trace = True and not g.unitTesting
        verbose = True
        c, p = self.c, self.c.p
        tree = c.frame.tree
        if self.changingText:
            if trace and verbose: g.trace('already changing')
            return
        if tree.tree_select_lockout:
            if trace and verbose: g.trace('selecting lockout')
            return
        if tree.selecting:
            if trace and verbose: g.trace('selecting')
            return
        if tree.redrawing:
            if trace and verbose: g.trace('redrawing')
            return
        if not p:
            if trace: g.trace('*** no p')
            return
        newInsert = self.getInsertPoint()
        newSel = self.getSelectionRange()
        newText = self.getAllText() # Converts to unicode.
        # Get the previous values from the VNode.
        oldText = p.b
        if oldText == newText:
            # This can happen as the result of undo.
            # g.error('*** unexpected non-change')
            return
        # g.trace('**',len(newText),p.h,'\n',g.callers(8))
        # oldIns  = p.v.insertSpot
        i, j = p.v.selectionStart, p.v.selectionLength
        oldSel = (i, i + j)
        if trace: g.trace('oldSel', oldSel, 'newSel', newSel)
        oldYview = None
        undoType = 'Typing'
        c.undoer.setUndoTypingParams(p, undoType,
            oldText=oldText, newText=newText,
            oldSel=oldSel, newSel=newSel, oldYview=oldYview)
        # Update the VNode.
        p.v.setBodyString(newText)
        if True:
            p.v.insertSpot = newInsert
            i, j = newSel
            i, j = self.toPythonIndex(i), self.toPythonIndex(j)
            if i > j: i, j = j, i
            p.v.selectionStart, p.v.selectionLength = (i, j - i)
        # No need to redraw the screen.
        c.recolor()
        if g.app.qt_use_tabs:
            if trace: g.trace(c.frame.top)
        if not c.changed and c.frame.initComplete:
            c.setChanged(True)
        c.frame.body.updateEditors()
        c.frame.tree.updateIcon(p)
    #@+node:ekr.20170511053143.8: *4* ctm.Generic high-level interface
    # These call only wrapper methods.
    #@+node:ekr.20170511053143.9: *5* ctm.Enable/disable
    def disable(self):
        self.enabled = False

    def enable(self, enabled=True):
        self.enabled = enabled
    #@+node:ekr.20170511053143.10: *5* ctm.Clipboard
    def clipboard_append(self, s):
        s1 = g.app.gui.getTextFromClipboard()
        g.app.gui.replaceClipboardWith(s1 + s)

    def clipboard_clear(self):
        g.app.gui.replaceClipboardWith('')
    #@+node:ekr.20170511053143.11: *5* ctm.setFocus (to do)
    def setFocus(self):
        '''CursesTextMixin'''
        ###
            # trace = (False or g.app.trace_focus) and not g.unitTesting
            # if trace: print('BaseQTextWrapper.setFocus', self.widget)
            # # Call the base class
            # assert isinstance(self.widget, (
                # QtWidgets.QTextBrowser,
                # QtWidgets.QLineEdit,
                # QtWidgets.QTextEdit,
                # Qsci and Qsci.QsciScintilla,
            # )), self.widget
            # QtWidgets.QTextBrowser.setFocus(self.widget)
    #@+node:ekr.20170511053143.12: *5* ctm.Generic text
    #@+node:ekr.20170511053143.13: *6* ctm.appendText
    def appendText(self, s):
        '''CursesTextMixin'''
        s2 = self.getAllText()
        self.setAllText(s2 + s)
        self.setInsertPoint(len(s2))
    #@+node:ekr.20170511053143.14: *6* ctm.delete
    def delete(self, i, j=None):
        '''CursesTextMixin'''
        i = self.toPythonIndex(i)
        if j is None: j = i + 1
        j = self.toPythonIndex(j)
        # This allows subclasses to use this base class method.
        if i > j: i, j = j, i
        s = self.getAllText()
        self.setAllText(s[: i] + s[j:])
        # Bug fix: Significant in external tests.
        self.setSelectionRange(i, i, insert=i)
    #@+node:ekr.20170511053143.15: *6* ctm.deleteTextSelection
    def deleteTextSelection(self):
        '''CursesTextMixin'''
        i, j = self.getSelectionRange()
        self.delete(i, j)
    #@+node:ekr.20170511053143.16: *6* ctm.get
    def get(self, i, j=None):
        '''CursesTextMixin'''
        # 2012/04/12: fix the following two bugs by using the vanilla code:
        # https://bugs.launchpad.net/leo-editor/+bug/979142
        # https://bugs.launchpad.net/leo-editor/+bug/971166
        s = self.getAllText()
        i = self.toPythonIndex(i)
        j = self.toPythonIndex(j)
        return s[i: j]
    #@+node:ekr.20170511053143.17: *6* ctm.getLastPosition & getLength
    def getLastPosition(self, s=None):
        '''CursesTextMixin'''
        return len(self.getAllText()) if s is None else len(s)

    def getLength(self, s=None):
        '''CursesTextMixin'''
        return len(self.getAllText()) if s is None else len(s)
    #@+node:ekr.20170511053143.18: *6* ctm.getSelectedText
    def getSelectedText(self):
        '''CursesTextMixin'''
        i, j = self.getSelectionRange()
        if i == j:
            return ''
        else:
            s = self.getAllText()
            return s[i: j]
    #@+node:ekr.20170511053143.19: *6* ctm.insert
    def insert(self, i, s):
        '''CursesTextMixin'''
        s2 = self.getAllText()
        i = self.toPythonIndex(i)
        self.setAllText(s2[: i] + s + s2[i:])
        self.setInsertPoint(i + len(s))
        return i
    #@+node:ekr.20170511053143.20: *6* ctm.seeInsertPoint
    def seeInsertPoint(self):
        '''Ensure the insert point is visible.'''
        self.see(self.getInsertPoint())
            # getInsertPoint defined in client classes.
    #@+node:ekr.20170511053143.21: *6* ctm.selectAllText
    def selectAllText(self, s=None):
        '''CursesTextMixin.'''
        self.setSelectionRange(0, self.getLength(s))
    #@+node:ekr.20170511053143.22: *6* ctm.toPythonIndex
    def toPythonIndex(self, index, s=None):
        '''CursesTextMixin'''
        if s is None:
            s = self.getAllText()
        i = g.toPythonIndex(s, index)
        # g.trace(index,len(s),i,s[i:i+10])
        return i
    #@+node:ekr.20170511053143.23: *6* ctm.toPythonIndexRowCol
    def toPythonIndexRowCol(self, index):
        '''CursesTextMixin'''
        s = self.getAllText()
        i = self.toPythonIndex(index)
        row, col = g.convertPythonIndexToRowCol(s, i)
        return i, row, col
    #@+node:ekr.20170511053143.24: *5* ctm.rememberSelectionAndScroll
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
    #@+node:ekr.20170511053143.25: *5* ctm.tag_configure
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
    #@-others
#@+node:ekr.20170511053048.1: *3* class CursesLineEditWrapper(CursesTextMixin)
class CursesLineEditWrapper(CursesTextMixin):
    '''
    A class to wrap CursesLineEdit widgets.

    The CursesHeadlineWrapper class is a subclass that merely
    redefines the do-nothing check method here.
    '''
    #@+others
    #@+node:ekr.20170511053048.2: *4* clew.Birth
    def __init__(self, widget, name, c=None):
        '''Ctor for QLineEditWrapper class.'''
        # g.trace('(QLineEditWrapper):widget',name,self.widget)
        CursesTextMixin.__init__(self, c)
            # Init the base class.
        self.widget = widget
        self.name = name
        self.baseClassName = 'QLineEditWrapper'

    def __repr__(self):
        return '<QLineEditWrapper: widget: %s' % (self.widget)

    __str__ = __repr__
    #@+node:ekr.20170511053048.3: *4* clew.check
    def check(self):
        '''
        QLineEditWrapper.
        '''
        return True
    #@+node:ekr.20170511053048.4: *4* clew.Widget-specific overrides (to do)
    # The CursesTextMixin class calls these methods.
    #@+node:ekr.20170511053048.5: *5* clew.getAllText
    def getAllText(self):
        '''CursesHeadlineWrapper.'''
        if self.check():
            w = self.widget
            s = w.text() ###
            return g.u(s)
        else:
            return ''
    #@+node:ekr.20170511053048.6: *5* clew.getInsertPoint
    def getInsertPoint(self):
        '''CursesHeadlineWrapper.'''
        if self.check():
            i = self.widget.cursorPosition() ###
            return i
        else:
            return 0
    #@+node:ekr.20170511053048.7: *5* clew.getSelectionRange
    def getSelectionRange(self, sort=True):
        '''CursesHeadlineWrapper.'''
        w = self.widget
        if self.check():
            if w.hasSelectedText(): ###
                i = w.selectionStart()
                s = w.selectedText()
                s = g.u(s)
                j = i + len(s)
            else:
                i = j = w.cursorPosition() ###
            return i, j
        else:
            return 0, 0
    #@+node:ekr.20170511053048.8: *5* clew.hasSelection
    def hasSelection(self):
        '''CursesHeadlineWrapper.'''
        if self.check():
            return self.widget.hasSelectedText() ###
        else:
            return False
    #@+node:ekr.20170511053048.9: *5* clew.see & seeInsertPoint
    def see(self, i):
        '''CursesHeadlineWrapper.'''
        pass

    def seeInsertPoint(self):
        '''CursesHeadlineWrapper.'''
        pass
    #@+node:ekr.20170511053048.10: *5* clew.setAllText
    def setAllText(self, s):
        '''Set all text of a Qt headline widget.'''
        if self.check():
            w = self.widget
            w.setText(s) ###
    #@+node:ekr.20170511053048.11: *5* clew.setFocus
    def setFocus(self):
        '''CursesHeadlineWrapper.'''
        if self.check():
            g.app.gui.set_focus(self.c, self.widget)
    #@+node:ekr.20170511053048.12: *5* clew.setInsertPoint
    def setInsertPoint(self, i, s=None):
        '''CursesHeadlineWrapper.'''
        if not self.check(): return
        w = self.widget
        if s is None:
            s = w.text() ###
            s = g.u(s)
        i = self.toPythonIndex(i)
        i = max(0, min(i, len(s)))
        w.setCursorPosition(i) ###
    #@+node:ekr.20170511053048.13: *5* clew.setSelectionRange
    def setSelectionRange(self, i, j, insert=None, s=None):
        '''CursesHeadlineWrapper.'''
        if not self.check(): return
        w = self.widget
        if i > j: i, j = j, i
        if s is None:
            s = w.text()
            s = g.u(s)
        n = len(s)
        i = self.toPythonIndex(i)
        j = self.toPythonIndex(j)
        i = max(0, min(i, n))
        j = max(0, min(j, n))
        if insert is None:
            insert = j
        else:
            insert = self.toPythonIndex(insert)
            insert = max(0, min(insert, n))
        if i == j:
            w.setCursorPosition(i) ###
        else:
            length = j - i
            # Set selection is a QLineEditMethod
            if insert < j:
                w.setSelection(j, -length) ###
            else:
                w.setSelection(i, length) ###
    # setSelectionRangeHelper = setSelectionRange
    #@-others
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
            assert isinstance(p, leoNodes.Position)
            assert p, g.callers()
            content = p.h
        else:
            content = self.content
        return len(content)
        
    def __repr__ (self):
        if native:
            p = self.content
            assert isinstance(p, leoNodes.Position)
            assert p, g.callers()
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
    #@+node:ekr.20170516143718.1: *5* LeoTreeData.XXX__getitem__
    def XXX__getitem__(self, n):
        '''Return the n'th item in this tree.'''
        trace = True
        verbose = False
        ### p.threadNext
            # if p.v.children:
                # p.moveToFirstChild()
            # elif p.hasNext():
                # p.moveToNext()
            # else:
                # p.moveToParent()
                # while p:
                    # if p.hasNext():
                        # p.moveToNext()
                        # break #found
                    # p.moveToParent()
        # if trace: g.trace('ENTRY', self, n)
        parent = self
        child_index = 0
        stack = [(self, 0),] # (parent, child_index)
        i = 0
        node = self._children[0]
        while node:
            progress = i
            if i == n:
                if trace: g.trace('FOUND', n, node)
                return node
            if trace and verbose: g.trace('NOT FOUND', node)
            ### if p.v.children: p.moveToFirstChild()
            if node._children:
                stack.append((node, 0),)
                parent = node
                child_index = 0
                node = node._children[0]
            ### elif p.hasNext(): p.moveToNext()
            elif child_index < len(parent._children):
                node = parent._children[child_index]
                child_index += 1
            else:
                ### p.moveToParent()
                node, junk = stack.pop()
                if not stack:
                    assert node == self, repr(node)
                    if trace: g.trace('NOT FOUND', n)
                    return None
                parent, childIndex = stack[-1]
                ### while p:
                while node:
                    ### if p.hasNext():
                    if child_index < len(parent._children):
                        # p.moveToNext()
                        node = parent._children[child_index]
                        break
                    ### p.moveToParent()
                    node, junk = stack.pop()
                    if not stack:
                        assert node == self, repr(node)
                        if trace: g.trace('NOT FOUND', n)
                        return None
                    parent, childIndex = stack[-1]
            i += 1
            assert progress+1 == i, repr(node)
        return None
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
    #@+node:ekr.20170518103807.6: *5* LeoTreeData.find_depth (Test)
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
    #@+node:ekr.20170516085427.2: *5* LeoTreeData.get_children (test)
    def get_children(self):
        
        if native:
            p = self.content
            return p.children()
        else:
            return self._children
    #@+node:ekr.20170518103807.11: *5* LeoTreeData.get_parent (ok)
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
        
        # g.trace('LeoTreeData', g.callers())
        if self.CHILDCLASS:
            cld = self.CHILDCLASS
        else:
            cld = type(self)
        child = cld(parent=self, *args, **keywords)
        self._children.append(child)
        ### return weakref.proxy(child)
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
        ### return weakref.proxy(child)
        return child
    #@+node:ekr.20170516085427.5: *5* LeoTreeData.remove_child (test)
    def remove_child(self, child):
        
        if native:
            p = self.content
            g.trace('LeoTreeData', p.h, g.callers())
            p.doDelete()
            ### self._children = [z for z in self._children if z != child]
        else:
            self._children = [z for z in self._children if z != child]
                # May be useful when child is cloned.
    #@+node:ekr.20170518103807.21: *5* LeoTreeData.set_content (ok)
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
                assert isinstance(p, leoNodes.Position), repr(content)
                assert p, g.callers()
                self.content = content.copy()
        else:
            self.content = content
    #@+node:ekr.20170516085427.6: *5* LeoTreeData.set_parent (ok)
    def set_parent(self, parent):

        # g.trace('LeoTreeData', parent, g.callers())
        self._parent = parent
        
    #@+node:ekr.20170518103807.24: *5* LeoTreeData.walk_tree (native & original)
    if native:

        def walk_tree(self,
            only_expanded=True,
            ignore_root=True,
            sort=None,
            sort_function=None,
        ):
            trace = True
            p = self.content.copy()
            if trace: g.trace('===== LeoTreeData: only_expanded:', only_expanded, p.h)
            if not ignore_root:
                yield self
            if only_expanded:
                while p:
                    if p.has_children() and p.isExpanded():
                        p.moveToFirstChild()
                        yield LeoTreeData(p.copy())
                    elif p.next():
                        p.moveToNext()
                        yield LeoTreeData(p.copy())
                    elif p.parent():
                        p.moveToParent()
                        yield LeoTreeData(p.copy())
                    else:
                        return # raise StopIteration
            else:
                while p:
                    yield LeoTreeData(p.copy())
                    p.moveToThreadNext()
    elif 0: 
        
        ### TreeData.walk_tree
        def walk_tree(self, only_expanded=True, ignore_root=True, sort=None, sort_function=None):

            import collections
            trace = True
            if sort is None:
                sort = self.sort
            if sort_function is None:
                sort_function = self.sort_function
            if self.sort_function_wrapper and sort_function:
               _this_sort_function = self.create_wrapped_sort_function(sort_function)
            else:
                _this_sort_function = sort_function
            key = _this_sort_function
            if not ignore_root:
                yield self
            nodes_to_yield = collections.deque() # better memory management than a list for pop(0)
            if self.expanded or not only_expanded:
                if sort:
                    # This and the similar block below could be combined into a nested function
                    if key:
                        nodes_to_yield.extend(sorted(self.get_children(), key=key,))
                    else:
                        nodes_to_yield.extend(sorted(self.get_children()))
                else:
                    nodes_to_yield.extend(self.get_children())
                while nodes_to_yield:
                    child = nodes_to_yield.popleft()
                    if child.expanded or not only_expanded:
                        # This and the similar block above could be combined into a nested function
                        if sort:
                            if key:
                                # must be reverse because about to use extendleft() below.
                                nodes_to_yield.extendleft(sorted(child.get_children(), key=key, reverse=True))
                            else:
                                nodes_to_yield.extendleft(sorted(child.get_children(), reverse=True))
                        else:
                            yield_these = list(child.get_children())
                            yield_these.reverse()
                            nodes_to_yield.extendleft(yield_these)
                            del yield_these
                    if trace: g.trace(child)
                    yield child
    #@+node:ekr.20170519030221.1: *5* TreeData.XXX_walk_tree (REF)
    #@+node:ekr.20170518103807.1: *4* From class TreeData (object)
    if 0:
        #@+others
        #@+node:ekr.20170518103807.2: *5* TreeData.__init__ (Ref)
        # def __init__(self,
            # content=None,
            # parent=None,
            # selected=False,
            # selectable=True,
            # highlight=False,
            # expanded=True,
            # ignore_root=True,
            # sort_function=None,
        # ):
            # self.set_parent(parent)
                # # EKR: set self._parent to None or weakref.proxy(parent)
            # self.set_content(content)
                # # EKR: sets self.content.
            # # EKR: other ivars.
            # self.selectable = selectable
            # self.selected = selected
            # self.highlight = highlight
            # self.expanded = expanded
            # self._children = []
            # self.ignore_root = ignore_root
            # self.sort = False
            # self.sort_function = sort_function
            # self.sort_function_wrapper = True
        #@+node:ekr.20170518103807.3: *5* TreeData._get_children_list (used?)
        def _get_children_list(self):
            g.trace('LeoTreeData', g.callers())
            return self._children

        #@+node:ekr.20170518103807.8: *5* TreeData.get_children_objects (used?)
        def get_children_objects(self):
            g.trace('LeoTreeData', g.callers())
            return self._children[:]
        #@+node:ekr.20170516085844.1: *5* TreeData.get_content (never called)
        def get_content(self):
            # Same as TreeData.get_content, but could be tweaked.
            g.trace('LeoTreeData', self.content, g.callers())
            return self.content
        #@+node:ekr.20170518103807.10: *5* TreeData.get_content_for_display (not used)
        def get_content_for_display(self):
            g.trace('===== LeoTreeData', g.callers())
            if native:
                p = self.content
                assert isinstance(p, leoNodes.Position)
                assert p, g.callers()
                return p.h
            else:
                return str(self.content)
        #@+node:ekr.20170518103807.13: *5* TreeData.has_children (To do)
        def has_children(self):
            
            g.trace('LeoTreeData', g.callers())
            return len(self._children) > 0
            
        #@+node:ekr.20170518103807.14: *5* TreeData.predicates (Test)
        #@+node:ekr.20170518103807.15: *6* TreeData.is_highlighted
        def is_highlighted(self):
            g.trace('LeoTreeData', g.callers())
            return self.highlight

        #@+node:ekr.20170518103807.16: *6* TreeData.is_last_sibling
        def is_last_sibling(self):
            g.trace('LeoTreeData', g.callers())
            if self.get_parent():
                return bool(list(self.get_parent().get_children())[-1] == self)
            else:
                return None

        #@+node:ekr.20170518103807.17: *6* TreeData.is_selected
        def is_selected(self):
            g.trace('LeoTreeData', g.callers())
            return self.selected

        #@+node:ekr.20170518103807.18: *5* TreeData.setters (To do)
        #@+node:ekr.20170518103807.23: *5* TreeData.walk_parents (used?)
        def walk_parents(self):
            g.trace('LeoTreeData', g.callers())
            p = self.get_parent()
            while p:
                yield p
                p = p.get_parent()
        #@-others
    #@-others
#@-others
#@-<< forward reference classes >>
#@+others
#@+node:ekr.20170501043944.1: **   top-level
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
    if isinstance(g.app.gui, CursesGui):
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
#@+node:ekr.20170420054211.1: ** class CursesApp (npyscreen.NPSApp)
class CursesApp(npyscreen.NPSApp):
    '''
    The *anonymous* npyscreen application object, created from
    CGui.runMainLoop. This is *not* g.app.
    '''
    
    if 0: # Not needed
        def __init__(self):
            g.trace('CursesApp')
            npyscreen.NPSApp.__init__(self)
                # Init the base class.

    def main(self):
        '''
        Called automatically from the ctor.
        Create and start Leo's singleton npyscreen window.
        '''
        g.app.gui.run()
#@+node:ekr.20170501024433.1: ** class CursesBody (leoFrame.LeoBody)
class CursesBody (leoFrame.LeoBody):
    '''
    A class that represents curses body pane.
    This is c.frame.body.
    '''
    
    def __init__(self, c):
        
        # g.trace('CursesBody', c.frame)
        leoFrame.LeoBody.__init__(self, frame=c.frame, parentFrame=None)
            # Init the base class.
        self.c = c
        self.colorizer = leoFrame.NullColorizer(c)
        self.widget = None
        self.wrapper = None # Set in createCursesBody.
#@+node:ekr.20170419105852.1: ** class CursesFrame (leoFrame.LeoFrame)
class CursesFrame (leoFrame.LeoFrame):
    '''The LeoFrame when --gui=curses is in effect.'''
    
    #@+others
    #@+node:ekr.20170501155347.1: *3* CFrame.birth
    def __init__ (self, c, title):
        
        # g.trace('CursesFrame', c.shortFileName())
        leoFrame.LeoFrame.instances += 1 # Increment the class var.
        leoFrame.LeoFrame.__init__(self, c, gui=g.app.gui)
            # Init the base class.
        assert c and self.c == c
        c.frame = self # Bug fix: 2017/05/10.
        self.log = CursesLog(c)
        g.app.gui.log = self.log
        self.title = title
        # Standard ivars.
        self.ratio = self.secondary_ratio = 0.0
        # Widgets
        self.top = CursesTopFrame(c)
        self.body = CursesBody(c)
        self.menu = CursesMenu(c)
        self.miniBufferWidget = None
        self.statusLine = g.NullObject() ###
        assert self.tree is None, self.tree
        self.tree = CursesTree(c)
        # npyscreen widgets.
        self.body_widget = None
        self.log_widget = None
        self.minibuffer_widget = None
        self.tree_widget = None
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
    #@+node:ekr.20170420163932.1: *4* CFrame.finishCreate (more work may be needed)
    def finishCreate(self):
        # g.trace('CursesFrame', self.c.shortFileName())
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
            ### self.createSplitterComponents()
            # self.createStatusLine() # A base class method.
            ### self.miniBufferWidget = qt_text.QMinibufferWrapper(c)
            ### c.bodyWantsFocus()
    #@+node:ekr.20170501161029.1: *3* CFrame.must be defined in subclasses
    def bringToFront(self):
        pass
        
    def contractPane(self, event=None):
        pass

    def deiconify(self):
        pass
            
    def destroySelf(self):
        pass

    def getFocus(self):
        pass ### To do
        # return g.app.gui.get_focus(self.c)

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
        g.pr("CursesFrame oops:", g.callers(4), "should be overridden in subclass")

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
    #@-others
#@+node:ekr.20170419094731.1: ** class CursesGui (leoGui.LeoGui)
class CursesGui(leoGui.LeoGui):
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
            # The singleton CursesApp instance.
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
        self.key_handler = CursesKeyHandler()

    #@+others
    #@+node:ekr.20170504112655.1: *3* CGui.clipboard (to do)
    #@+node:ekr.20170504112744.2: *4* CGui.replaceClipboardWith (to do)
    def replaceClipboardWith(self, s):
        '''Replace the clipboard with the string s.'''
        pass
        ###
            # cb = self.qtApp.clipboard()
            # if cb:
                # s = g.toUnicode(s)
                # QtWidgets.QApplication.processEvents()
                # # Fix #241: QMimeData object error
                # cb.setText(QString(s))
                # QtWidgets.QApplication.processEvents()
                # # g.trace(len(s), type(s), s[: 25])
            # else:
                # g.trace('no clipboard!')
    #@+node:ekr.20170504112744.3: *4* CGui.getTextFromClipboard
    def getTextFromClipboard(self):
        '''Get a unicode string from the clipboard.'''
        return ''
        ###
            # cb = self.qtApp.clipboard()
            # if cb:
                # QtWidgets.QApplication.processEvents()
                # s = cb.text()
                # # g.trace(len(s), type(s), s[: 25])
                # # Fix bug 147: Python 3 clipboard encoding
                # s = g.u(s)
                    # # Don't call g.toUnicode here!
                    # # s is a QString, which isn't exactly a unicode string!
                # return s
            # else:
                # g.trace('no clipboard!')
                # return ''
    #@+node:ekr.20170504112744.4: *4* CGui.setClipboardSelection
    def setClipboardSelection(self, s):
        '''Set the clipboard selection to s.'''
        ###
            # if s:
                # # This code generates a harmless, but annoying warning on PyQt5.
                # cb = self.qtApp.clipboard()
                # cb.setText(QString(s), mode=cb.Selection)
    #@+node:ekr.20170502083158.1: *3* CGui.createCursesTop & helpers
    def createCursesTop(self):
        '''Create the top-level curses Form.'''
        trace = False and not g.unitTesting
        # Assert the key relationships required by the startup code.
        assert self == g.app.gui
        c = g.app.log.c
        assert c == g.app.windowList[0].c
        assert isinstance(c.frame, CursesFrame), repr(c.frame)
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
        g.es(form)
        return form
    #@+node:ekr.20170502084106.1: *4* CGui.createCursesBody
    def createCursesBody(self, c, form):
        '''
        Create the curses body widget in the given curses Form.
        Populate it with c.p.b.
        '''
        w = form.add(
            npyscreen.MultiLineEditableBoxed,
            max_height=8, # Subtract 4 lines
            name='Body Pane',
            footer="Press i or o to insert text", 
            values=g.splitLines(c.p.b), 
            slow_scroll=True,
        )
        # Link and check.
        assert isinstance(w, npyscreen.MultiLineEditableBoxed), repr(w)
        assert isinstance(c.frame, leoFrame.LeoFrame), repr(c.frame)
            # The generic LeoFrame class
        assert isinstance(c.frame.body, leoFrame.LeoBody), repr(c.frame.body)
            # The generic LeoBody class
        assert not hasattr(c.frame.tree, 'bodyWidget'), repr(c.frame.tree.bodyWidget)
            # Used only by the Qt gui.
        assert c.frame.body_widget is None, repr(c.frame.body_widget)
        c.frame.body_widget = w
        c.frame.body.widget = w
        assert c.frame.body.wrapper is None, repr(c.frame.body.wrapper)
        c.frame.body.wrapper = CursesTextWrapper(c, 'body', w)
    #@+node:ekr.20170502083613.1: *4* CGui.createCursesLog
    def createCursesLog(self, c, form):
        '''
        Create the curses log widget in the given curses Form.
        Populate the widget with the queued log messages.
        '''
        w = form.add(
            npyscreen.MultiLineEditableBoxed,
            max_height=8, # Subtract 4 lines
            name='Log Pane',
            footer="Press i or o to insert text", 
            values=[s for s, color in self.wait_list], 
            slow_scroll=False,
        )
        # Clear the wait list and disable it.
        self.wait_list = []
        self.log_inited = True
        # Link and check...
        assert isinstance(w, npyscreen.MultiLineEditableBoxed), repr(w)
        assert isinstance(self.log, CursesLog), repr(self.log)
        self.log.widget = w
        assert isinstance(c.frame, leoFrame.LeoFrame), repr(c.frame)
            # The generic LeoFrame class
        assert c.frame.log_widget is None, repr(c.frame.log_widget)
        c.frame.log_widget = w
    #@+node:ekr.20170502084249.1: *4* CGui.createCursesMinibuffer
    def createCursesMinibuffer(self, c, form):
        '''Create the curses minibuffer widget in the given curses Form.'''
        
        class MiniBufferBox(npyscreen.BoxTitle):
            '''An npyscreen class representing Leo's minibuffer, with binding.'''
            # pylint: disable=used-before-assignment
            _contained_widget = LeoMiniBuffer
        
        w = form.add(MiniBufferBox, name='Mini-buffer', max_height=3)
        # Link and check...
        assert isinstance(w, MiniBufferBox)
        mini_buffer = w._my_widgets[0]
        assert isinstance(mini_buffer, LeoMiniBuffer), repr(mini_buffer)
        mini_buffer.leo_c = c
        assert isinstance(c.frame, leoFrame.LeoFrame), repr(c.frame)
            # The generic LeoFrame class
        assert c.frame.minibuffer_widget is None
        c.frame.minibuffer_widget = mini_buffer
    #@+node:ekr.20170502083754.1: *4* CGui.createCursesTree
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
        w = form.add(
            BoxTitleTree,
            max_height=8, # Subtract 4 lines
            name='Tree Pane',
            footer="d: delete node; i: insert node; h: edit (return to end)",
            values=hidden_root_node, 
            slow_scroll=False,
        )
        # Link and check...
        assert isinstance(w, BoxTitleTree), w
        leo_tree = w._my_widgets[0]
        assert isinstance(leo_tree, LeoMLTree), repr(leo_tree)
            # leo_tree is a LeoMLTree.
        leo_tree.leo_c = c
        if native:
            leo_tree.values = LeoValues(c=c, tree = leo_tree)
        assert getattr(leo_tree, 'hidden_root_node') is None, leo_tree
        leo_tree.hidden_root_node = hidden_root_node
        assert isinstance(c.frame, leoFrame.LeoFrame), repr(c.frame)
            # CursesFrame is a LeoFrame
        assert isinstance(c.frame.tree, leoFrame.LeoTree), repr(c.frame.tree)
            # CursesTree is a LeoTree
        assert c.frame.tree.canvas is None, repr(c.frame.canvas)
            # A standard ivar, used by Leo's core.
        c.frame.canvas = leo_tree
            # A LeoMLTree.
        assert not hasattr(c.frame.tree, 'treeWidget'), repr(c.frame.tree.treeWidget)
        c.frame.tree.treeWidget = leo_tree
        assert c.frame.tree_widget is None, repr(c.frame.tree_widget)
        c.frame.tree_widget = leo_tree
            # A LeoMLTree
        assert c.frame.tree.tree_widget is None
        c.frame.tree.tree_widget = leo_tree
            # Set CursesTree.tree_widget.
    #@+node:ekr.20170419110052.1: *3* CGui.createLeoFrame
    def createLeoFrame(self, c, title):
        '''
        Create a LeoFrame for the current gui.
        Called from Leo's core (c.initObjects).
        '''
        return CursesFrame(c, title)
    #@+node:ekr.20170502103338.1: *3* CGui.destroySelf
    def destroySelf(self):
        '''
        Terminate the curses gui application.
        Leo's core calls this only if the user agrees to terminate the app.
        '''
        sys.exit(0)
    #@+node:ekr.20170502021145.1: *3* CGui.dialogs (to do)
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
    #@+node:ekr.20170430114709.1: *3* CGui.do_key
    def do_key(self, ch_i):
        
        return self.key_handler.do_key(ch_i)
    #@+node:ekr.20170514060742.1: *3* CGui.fonts
    def getFontFromParams(self, family, size, slant, weight, defaultSize=12):
        # g.trace('CursesGui', g.callers())
        return None
    #@+node:ekr.20170502101347.1: *3* CGui.get/set_focus (to do)
    def get_focus(self, *args, **keys):
        
        # Careful during startup.
        return getattr(g.app.gui.curses_form, 'editw', None)

    def set_focus(self, *args, **keys):
        pass
    #@+node:ekr.20170501032447.1: *3* CGui.init_logger
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
    #@+node:ekr.20170504052119.1: *3* CGui.isTextWrapper
    def isTextWrapper(self, w):
        '''Return True if w is a Text widget suitable for text-oriented commands.'''
        return w and getattr(w, 'supportsHighLevelInterface', None)
    #@+node:ekr.20170504052042.1: *3* CGui.oops
    def oops(self):
        '''Ignore do-nothing methods.'''
        g.pr("CursesGui oops:", g.callers(4), "should be overridden in subclass")
    #@+node:ekr.20170502020354.1: *3* CGui.run
    def run(self):
        '''
        Create and run the top-level curses form.
        
        '''
        self.top_form = self.createCursesTop()
        self.top_form.edit()
    #@+node:ekr.20170419140914.1: *3* CGui.runMainLoop
    def runMainLoop(self):
        '''The curses gui main loop.'''
        # Do NOT change g.app!
        g.trace('native', native)
        self.curses_app = CursesApp()
        self.curses_app.run()
            # run calls CApp.main(), which calls CGui.run().
        g.trace('DONE')
        # pylint: disable=no-member
        # endwin *does* exist.
        curses.endwin()
    #@+node:ekr.20170510074755.1: *3* CGui.test
    def test(self):
        '''A place to put preliminary tests.'''
    #@-others
#@+node:ekr.20170511053415.1: ** class CursesHeadlineWrapper (CursesLineEditWrapper)
class CursesHeadlineWrapper(CursesLineEditWrapper):
    '''
    A wrapper class for CursesLineEdit widgets in CursesTree.

    This class just redefines the check method.
    '''

    #@+others
    #@+node:ekr.20170511053415.2: *3* chw.Birth
    def __init__(self, c, item, name, widget):
        '''The ctor for the CursesHeadlineWrapper class.'''
        # g.trace('(CursesHeadlineWrapper)', item, widget)
        assert isinstance(widget, LeoTreeLine), repr(widget)
        CursesLineEditWrapper.__init__(self, widget, name, c)
            # Init the base class.
        # Set ivars.
        self.c = c
        self.item = item
        self.name = name
        self.widget = widget
        ### g.app.gui.setFilter(c, self.widget, self, tag=name)

    def __repr__(self):
        return 'CursesHeadlineWrapper: %s' % id(self)
    #@+node:ekr.20170511053415.3: *3* chw.check
    def check(self):
        '''Return True if the tree item exists and its edit widget exists.'''
        return False ### Not ready yet.
        ###
            # trace = False and not g.unitTesting
            # tree = self.c.frame.tree
            # e = tree.treeWidget.itemWidget(self.item, 0)
            # valid = tree.isValidItem(self.item)
            # result = valid and e == self.widget
            # if trace: g.trace('result %s self.widget %s itemWidget %s' % (
                # result, self.widget, e))
            # return result
    #@-others
#@+node:ekr.20170430114840.1: ** class CursesKeyHandler (object)
class CursesKeyHandler (object):

    #@+others
    #@+node:ekr.20170430114930.1: *3* CKey.do_key & helpers
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
    #@+node:ekr.20170430115131.4: *4* CKey.char_to_tk_name
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
    #@+node:ekr.20170430115131.2: *4* CKey.create_key_event
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
        ### Alt keys apparently never generated.
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
    #@+node:ekr.20170430115030.1: *4* CKey.is_key_event
    def is_key_event(self, ch_i):
        # pylint: disable=no-member
        return ch_i not in (curses.KEY_MOUSE,)
    #@+node:ekr.20170430115131.3: *4* CKey.to_key
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
#@+node:ekr.20170419143731.1: ** class CursesLog (leoFrame.LeoLog)
class CursesLog (leoFrame.LeoLog):
    '''
    A class that represents curses log pane.
    This is c.frame.log.
    '''
    
    #@+others
    #@+node:ekr.20170419143731.4: *3* CLog.__init__
    def __init__(self, c):
        '''Ctor for CLog class.'''
        # g.trace('CursesLog')
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
                ### tw = c.frame.top.leo_ui.tabWidget
                ### The Qt.QTabWidget that holds all the tabs.
    #@+node:ekr.20170419143731.2: *3*  CLog.cmd (decorator)
    def cmd(name):
        '''Command decorator for the c.frame.log class.'''
        # pylint: disable=no-self-argument
        return g.new_cmd_decorator(name, ['c', 'frame', 'log'])
    #@+node:ekr.20170419143731.7: *3* CLog.clearLog
    @cmd('clear-log')
    def clearLog(self, event=None):
        '''Clear the log pane.'''
        # w = self.logCtrl.widget # w is a QTextBrowser
        # if w:
            # w.clear()
    #@+node:ekr.20170420035717.1: *3* CLog.enable/disable
    def disable(self):
        self.enabled = False

    def enable(self, enabled=True):
        self.enabled = enabled
    #@+node:ekr.20170420041119.1: *3* CLog.finishCreate
    def finishCreate(self):
        '''CursesLog.finishCreate.'''
        pass
    #@+node:ekr.20170513183826.1: *3* CLog.isLogWidget
    def isLogWidget(self, w):
        return w == self or w in list(self.contentsDict.values())
    #@+node:ekr.20170513184115.1: *3* CLog.orderedTabNames
    def orderedTabNames(self, LeoLog=None): # Unused: LeoLog
        '''Return a list of tab names in the order in which they appear in the QTabbedWidget.'''
        return []
        ### w = self.tabWidget
        ### return [w.tabText(i) for i in range(w.count())]
    #@+node:ekr.20170419143731.15: *3* CLog.put
    def put(self, s, color=None, tabName='Log', from_redirect=False):
        '''All output to the log stream eventually comes here.'''
        c, w = self.c, self.widget
        if not c or not c.exists:
            # logging.info('CLog.put: no c: %r' % s)
            pass
        elif w:
            values = w.get_values()
            values.append(s)
            w.set_values(values)
            w.update()
        else:
            pass
            # logging.info('CLog.put no w: %r' % s)
    #@+node:ekr.20170419143731.16: *3* CLog.putnl
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
#@+node:ekr.20170419111515.1: ** class CursesMenu (leoMenu.LeoMenu)
class CursesMenu (leoMenu.LeoMenu):

    def __init__ (self, c):
        
        dummy_frame = g.Bunch(c=c)
        leoMenu.LeoMenu.__init__(self, dummy_frame)
        self.c = c
        self.d = {}

    def oops(self):
        '''Ignore do-nothing methods.'''
        # g.pr("CursesMenu oops:", g.callers(4), "should be overridden in subclass")

        
#@+node:ekr.20170504034655.1: ** class CursesTextWrapper (leoFrame.StringTextWrapper)
class CursesTextWrapper(leoFrame.StringTextWrapper):
    '''
    A Wrapper class for Curses edit widgets classes.
    This is c.frame.body.wrapper or c.frame.log.wrapper.
    '''
    #@+others
    #@+node:ekr.20170504034655.2: *3* cw.ctor & helper
    def __init__(self, c, name, w):
        '''Ctor for CursesTextWrapper class'''
        super(CursesTextWrapper, self).__init__(c, name)
        ### self.c = c
        ### self.name = name
        ### self.supportsHighLevelInterface = True
            # A flag for k.masterKeyHandler and isTextWrapper.
        #
        self.changingText = False # A lockout for onTextChanged.
        self.enabled = True
        self.w = self.widget = w
        self.injectIvars(c)
            # These are used by Leo's core.
    #@+node:ekr.20170504034655.3: *4* cw.injectIvars
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
    #@+node:ekr.20170504034655.5: *3* cw.Event handlers (To do)
    # These are independent of the kind of Qt widget.
    #@+node:ekr.20170504034655.6: *4* cw.onCursorPositionChanged
    def onCursorPositionChanged(self, event=None):
        c = self.c
        name = c.widget_name(self)
        # Apparently, this does not cause problems
        # because it generates no events in the body pane.
        if name.startswith('body'):
            if hasattr(c.frame, 'statusLine'):
                c.frame.statusLine.update()
    #@+node:ekr.20170504034655.7: *4* cw.onTextChanged
    def onTextChanged(self):
        '''
        Update Leo after the body has been changed.

        self.selecting is guaranteed to be True during
        the entire selection process.
        '''
        # Important: usually w.changingText is True.
        # This method very seldom does anything.
        trace = False and not g.unitTesting
        verbose = False
        c = self.c; p = c.p
        tree = c.frame.tree
        if self.changingText:
            if trace and verbose: g.trace('already changing')
            return
        if tree.tree_select_lockout:
            if trace and verbose: g.trace('selecting lockout')
            return
        if tree.selecting:
            if trace and verbose: g.trace('selecting')
            return
        if tree.redrawing:
            if trace and verbose: g.trace('redrawing')
            return
        if not p:
            if trace: g.trace('*** no p')
            return
        newInsert = self.getInsertPoint()
        newSel = self.getSelectionRange()
        newText = self.getAllText() # Converts to unicode.
        # Get the previous values from the VNode.
        oldText = p.b
        if oldText == newText:
            # This can happen as the result of undo.
            # g.error('*** unexpected non-change')
            return
        # g.trace('**',len(newText),p.h,'\n',g.callers(8))
        # oldIns  = p.v.insertSpot
        i, j = p.v.selectionStart, p.v.selectionLength
        oldSel = (i, i + j)
        if trace: g.trace('oldSel', oldSel, 'newSel', newSel)
        oldYview = None
        undoType = 'Typing'
        c.undoer.setUndoTypingParams(p, undoType,
            oldText=oldText, newText=newText,
            oldSel=oldSel, newSel=newSel, oldYview=oldYview)
        # Update the VNode.
        p.v.setBodyString(newText)
        if True:
            p.v.insertSpot = newInsert
            i, j = newSel
            i, j = self.toPythonIndex(i), self.toPythonIndex(j)
            if i > j: i, j = j, i
            p.v.selectionStart, p.v.selectionLength = (i, j - i)
        # No need to redraw the screen.
        c.recolor()
        if g.app.qt_use_tabs:
            if trace: g.trace(c.frame.top)
        if not c.changed and c.frame.initComplete:
            c.setChanged(True)
        c.frame.body.updateEditors()
        c.frame.tree.updateIcon(p)
    #@+node:ekr.20170504034655.8: *3* cw.High-level interface
    if 0: ### Just use the StringTextWrapper methods
        #@+others
        #@+node:ekr.20170504035808.1: *4* curses-specific (To do)
        #@+node:ekr.20170504040309.2: *5* cw.delete (uses getAllText)
        def delete(self, i, j=None):
            
            # Generic
            i = self.toPythonIndex(i)
            if j is None: j = i + 1
            j = self.toPythonIndex(j)
            # This allows subclasses to use this base class method.
            if i > j: i, j = j, i
            s = self.getAllText()
            self.setAllText(s[: i] + s[j:])
            self.setSelectionRange(i, i, insert=i)
            ###
                # Avoid calls to setAllText
                # w = self.widget
                # if trace: g.trace(self.getSelectionRange())
                # i = self.toPythonIndex(i)
                # if j is None: j = i + 1
                # j = self.toPythonIndex(j)
                # if i > j: i, j = j, i
                # if trace: g.trace(i, j)
                # sb = w.verticalScrollBar()
                # pos = sb.sliderPosition()
                # cursor = w.textCursor()
                # try:
                    # self.changingText = True # Disable onTextChanged
                    # old_i, old_j = self.getSelectionRange()
                    # if i == old_i and j == old_j:
                        # # Work around an apparent bug in cursor.movePosition.
                        # cursor.removeSelectedText()
                    # elif i == j:
                        # pass
                    # else:
                        # # g.trace('*** using dubious code')
                        # cursor.setPosition(i)
                        # moveCount = abs(j - i)
                        # cursor.movePosition(cursor.Right, cursor.KeepAnchor, moveCount)
                        # w.setTextCursor(cursor) # Bug fix: 2010/01/27
                        # if trace:
                            # i, j = self.getSelectionRange()
                            # g.trace(i, j)
                        # cursor.removeSelectedText()
                        # if trace: g.trace(self.getSelectionRange())
                # finally:
                    # self.changingText = False
                # sb.setSliderPosition(pos)
        #@+node:ekr.20170504040309.3: *5* cw.flashCharacter (To do)
        def flashCharacter(self, i,
            bg='white',
            fg='red',
            flashes=3,
            delay=75,
        ):
            pass
            ###
                # # numbered color names don't work in Ubuntu 8.10, so...
                # if bg[-1].isdigit() and bg[0] != '#':
                    # bg = bg[: -1]
                # if fg[-1].isdigit() and fg[0] != '#':
                    # fg = fg[: -1]
                # # This might causes problems during unit tests.
                # # The selection point isn't restored in time.
                
                # if g.app.unitTesting:
                    # return
                # w = self.widget # A QTextEdit.
                # e = QtGui.QTextCursor
            
                # def after(func):
                    # QtCore.QTimer.singleShot(delay, func)
            
                # def addFlashCallback(self=self, w=w):
                    # i = self.flashIndex
                    # cursor = w.textCursor() # Must be the widget's cursor.
                    # cursor.setPosition(i)
                    # cursor.movePosition(e.Right, e.KeepAnchor, 1)
                    # extra = w.ExtraSelection()
                    # extra.cursor = cursor
                    # if self.flashBg: extra.format.setBackground(QtGui.QColor(self.flashBg))
                    # if self.flashFg: extra.format.setForeground(QtGui.QColor(self.flashFg))
                    # self.extraSelList = [extra] # keep the reference.
                    # w.setExtraSelections(self.extraSelList)
                    # self.flashCount -= 1
                    # after(removeFlashCallback)
            
                # def removeFlashCallback(self=self, w=w):
                    # w.setExtraSelections([])
                    # if self.flashCount > 0:
                        # after(addFlashCallback)
                    # else:
                        # w.setFocus()
            
                # self.flashCount = flashes
                # self.flashIndex = i
                # self.flashBg = None if bg.lower() == 'same' else bg
                # self.flashFg = None if fg.lower() == 'same' else fg
                # addFlashCallback()
        #@+node:ekr.20170504035640.1: *5* cw.getAllText (To do)
        def getAllText(self):

            return ''
            ###
                # w = self.widget
                # s = g.u(w.toPlainText())
                # return s
        #@+node:ekr.20170504040026.1: *5* cw.getInsertPoint (To do)
        def getInsertPoint(self):
            
            return 0
            ###
                # return self.widget.textCursor().position()
        #@+node:ekr.20170504040221.1: *5* cw.getSelectionRange (To do)
        def getSelectionRange(self, sort=True):
            
            return 0, 0
            ###
                # w = self.widget
                # tc = w.textCursor()
                # i, j = tc.selectionStart(), tc.selectionEnd()
                # return i, j
        #@+node:ekr.20170504040309.7: *5* cw.getX/YScrollPosition (To do)
        def getXScrollPosition(self):

            return 0
            ###
                # w = self.widget
                # sb = w.horizontalScrollBar()
                # return sb.sliderPosition()

        def getYScrollPosition(self):

            return 0
            ###
                # w = self.widget
                # sb = w.verticalScrollBar()
                # return sb.sliderPosition()
        #@+node:ekr.20170504040309.8: *5* cw.hasSelection (To do)
        def hasSelection(self):
            
            return False
            ###
                # return self.widget.textCursor().hasSelection()
        #@+node:ekr.20170504040309.9: *5* cw.insert (uses setAllText)
        def insert(self, i, s):
            
            s2 = self.getAllText()
            i = self.toPythonIndex(i)
            self.setAllText(s2[: i] + s + s2[i:])
            self.setInsertPoint(i + len(s))
            return i
            ### Avoid call to getAllText
                # w = self.widget
                # i = self.toPythonIndex(i)
                # cursor = w.textCursor()
                # try:
                    # self.changingText = True # Disable onTextChanged.
                    # cursor.setPosition(i)
                    # cursor.insertText(s)
                    # w.setTextCursor(cursor) # Bug fix: 2010/01/27
                # finally:
                    # self.changingText = False
        #@+node:ekr.20170504040309.14: *5* cw.see & seeInsertPoint (to do)
        def see(self, i):
            '''Make sure position i is visible.'''
            pass
            ###
                # trace = False and not g.unitTesting
                # w = self.widget
                # if trace:
                    # cursor = w.textCursor()
                    # g.trace('i', i, 'pos', cursor.position())
                        # # 'getInsertPoint',self.getInsertPoint())
                # w.ensureCursorVisible()

        def seeInsertPoint(self):
            '''Make sure the insert point is visible.'''
            pass
            ###
                # trace = False and not g.unitTesting
                # if trace: g.trace(self.getInsertPoint())
                # self.widget.ensureCursorVisible()
        #@+node:ekr.20170504034655.21: *5* cw.selectAllText (to do)
        def selectAllText(self, s=None):
            
            pass
            ###
                # self.setSelectionRange(0, self.getLength(s))
        #@+node:ekr.20170504040309.15: *5* cw.setAllText (to do)
        def setAllText(self, s):
            '''Set the text of body pane.'''
            pass
            ###
            # trace = False and not g.unitTesting
            # trace_time = True
            # c, w = self.c, self.widget
            # h = c.p.h if c.p else '<no p>'
            # if trace and not trace_time: g.trace(len(s), h)
            # try:
                # if trace and trace_time:
                    # t1 = time.time()
                # self.changingText = True # Disable onTextChanged.
                # w.setReadOnly(False)
                # w.setPlainText(s)
                # if trace and trace_time:
                    # delta_t = time.time() - t1
                    # g.trace('%4.2f sec. %6s chars %s' % (delta_t, len(s), h))
            # finally:
                # self.changingText = False
        #@+node:ekr.20170504034655.11: *5* cw.setFocus (to do)
        def setFocus(self):
            
            pass
            ###
                # # Call the base class
                # assert isinstance(self.widget, (
                    # QtWidgets.QTextBrowser,
                    # QtWidgets.QLineEdit,
                    # QtWidgets.QTextEdit,
                    # Qsci and Qsci.QsciScintilla,
                # )), self.widget
                # QtWidgets.QTextBrowser.setFocus(self.widget)
        #@+node:ekr.20170504040309.17: *5* cw.setSelectionRange (to do)
        def setSelectionRange(self, i, j, insert=None, s=None):
            '''Set the selection range and the insert point.'''
            pass
            ###
                # trace = False and not g.unitTesting
                # traceTime = False and not g.unitTesting
                # # Part 1
                # if traceTime: t1 = time.time()
                # w = self.widget
                # i = self.toPythonIndex(i)
                # j = self.toPythonIndex(j)
                # if s is None:
                    # s = self.getAllText()
                # n = len(s)
                # i = max(0, min(i, n))
                # j = max(0, min(j, n))
                # if insert is None:
                    # ins = max(i, j)
                # else:
                    # ins = self.toPythonIndex(insert)
                    # ins = max(0, min(ins, n))
                # if traceTime:
                    # delta_t = time.time() - t1
                    # if delta_t > 0.1: g.trace('part1: %2.3f sec' % (delta_t))
                # # Part 2:
                # if traceTime: t2 = time.time()
                # # 2010/02/02: Use only tc.setPosition here.
                # # Using tc.movePosition doesn't work.
                # tc = w.textCursor()
                # if i == j:
                    # tc.setPosition(i)
                # elif ins == j:
                    # # Put the insert point at j
                    # tc.setPosition(i)
                    # tc.setPosition(j, tc.KeepAnchor)
                # elif ins == i:
                    # # Put the insert point at i
                    # tc.setPosition(j)
                    # tc.setPosition(i, tc.KeepAnchor)
                # else:
                    # # 2014/08/21: It doesn't seem possible to put the insert point somewhere else!
                    # tc.setPosition(j)
                    # tc.setPosition(i, tc.KeepAnchor)
                # w.setTextCursor(tc)
                # # Fix bug 218: https://github.com/leo-editor/leo-editor/issues/218
                # if hasattr(g.app.gui, 'setClipboardSelection'):
                    # g.app.gui.setClipboardSelection(s[i:j])
                # # Remember the values for v.restoreCursorAndScroll.
                # v = self.c.p.v # Always accurate.
                # v.insertSpot = ins
                # if i > j: i, j = j, i
                # assert(i <= j)
                # v.selectionStart = i
                # v.selectionLength = j - i
                # v.scrollBarSpot = spot = w.verticalScrollBar().value()
                # if trace: g.trace('i: %s j: %s ins: %s spot: %s %s' % (i, j, ins, spot, v.h))
                # if traceTime:
                    # delta_t = time.time() - t2
                    # tot_t = time.time() - t1
                    # if delta_t > 0.1: g.trace('part2: %2.3f sec' % (delta_t))
                    # if tot_t > 0.1: g.trace('total: %2.3f sec' % (tot_t))

        setSelectionRangeHelper = setSelectionRange
        #@+node:ekr.20170504040309.18: *5* cw.setXScrollPosition (to do)
        def setXScrollPosition(self, pos):
            '''Set the position of the horizonatl scrollbar.'''
            pass
            ###
                # if pos is not None:
                    # w = self.widget
                    # sb = w.horizontalScrollBar()
                    # sb.setSliderPosition(pos)
        #@+node:ekr.20170504040309.19: *5* cw.setYScrollPosition (to do)
        def setYScrollPosition(self, pos):
            '''Set the vertical scrollbar position.'''
            pass
            ###
                # if pos is not None:
                    # w = self.widget
                    # sb = w.verticalScrollBar()
                    # sb.setSliderPosition(pos)
        #@+node:ekr.20170504035742.1: *4* generic (no changes)
        # These call only wrapper methods.
        #@+node:ekr.20170504034655.13: *5* cw.appendText
        def appendText(self, s):

            s2 = self.getAllText()
            self.setAllText(s2 + s)
            self.setInsertPoint(len(s2))
        #@+node:ekr.20170504034655.10: *5* cw.clipboard_append & clipboard_clear
        def clipboard_append(self, s):
            s1 = g.app.gui.getTextFromClipboard()
            g.app.gui.replaceClipboardWith(s1 + s)

        def clipboard_clear(self):
            g.app.gui.replaceClipboardWith('')
        #@+node:ekr.20170504034655.15: *5* cw.deleteTextSelection
        def deleteTextSelection(self):

            i, j = self.getSelectionRange()
            self.delete(i, j)
        #@+node:ekr.20170504034655.9: *5* cw.enable/disable
        def disable(self):
            self.enabled = False

        def enable(self, enabled=True):
            self.enabled = enabled
        #@+node:ekr.20170504034655.16: *5* cw.get
        def get(self, i, j=None):

            # 2012/04/12: fix the following two bugs by using the vanilla code:
            # https://bugs.launchpad.net/leo-editor/+bug/979142
            # https://bugs.launchpad.net/leo-editor/+bug/971166
            s = self.getAllText()
            i = self.toPythonIndex(i)
            j = self.toPythonIndex(j)
            return s[i: j]
        #@+node:ekr.20170504034655.17: *5* cw.getLastPosition & getLength
        def getLastPosition(self, s=None):

            return len(self.getAllText()) if s is None else len(s)

        def getLength(self, s=None):

            return len(self.getAllText()) if s is None else len(s)
        #@+node:ekr.20170504034655.4: *5* cw.getName
        def getName(self):
            return self.name # Essential.
        #@+node:ekr.20170504034655.18: *5* cw.getSelectedText
        def getSelectedText(self):

            i, j = self.getSelectionRange()
            if i == j:
                return ''
            else:
                s = self.getAllText()
                return s[i: j]
        #@+node:ekr.20170504034655.24: *5* cw.rememberSelectionAndScroll
        def rememberSelectionAndScroll(self):
            
            w = self
            v = self.c.p.v # Always accurate.
            v.insertSpot = w.getInsertPoint()
            i, j = w.getSelectionRange()
            if i > j: i, j = j, i
            assert(i <= j)
            v.selectionStart = i
            v.selectionLength = j - i
            v.scrollBarSpot = w.getYScrollPosition()
        #@+node:ekr.20170504040309.16: *5* cw.setInsertPoint
        def setInsertPoint(self, i, s=None):

            # Fix bug 981849: incorrect body content shown.
            # Use the more careful code in setSelectionRange.
            self.setSelectionRange(i=i, j=i, insert=i, s=s)
        #@+node:ekr.20170504034655.22: *5* cw.toPythonIndex
        def toPythonIndex(self, index, s=None):

            if s is None:
                s = self.getAllText()
            i = g.toPythonIndex(s, index)
            return i
        #@+node:ekr.20170504034655.23: *5* cw.toPythonIndexRowCol
        def toPythonIndexRowCol(self, index):

            s = self.getAllText()
            i = self.toPythonIndex(index)
            row, col = g.convertPythonIndexToRowCol(s, i)
            return i, row, col
        #@-others
    #@-others
#@+node:ekr.20170502093200.1: ** class CursesTopFrame (object)
class CursesTopFrame (object):
    '''A representation of c.frame.top.'''
    
    def __init__(self, c):
        # g.trace('CursesTopFrame', c)
        self.c = c
        
    def select(self, *args, **kwargs):
        pass # g.trace(args, kwargs)
        
    def findChild(self, *args, **kwargs):
        # Called by nested_splitter.py.
        return g.NullObject() ### Required, for now.

    def finishCreateLogPane(self, *args, **kwargs):
        pass # g.trace(args, kwargs)
#@+node:ekr.20170501024424.1: ** class CursesTree (leoFrame.LeoTree)
class CursesTree (leoFrame.LeoTree):
    '''
    A class that represents curses tree pane.
    
    This is the c.frame.tree instance.
    
    CGui.createCursesTree sets the c.frame.tree_widget
    '''
        
    #@+others
    #@+node:ekr.20170511111242.1: *3*  CTree.ctor
    class DummyFrame:
        def __init__(self, c):
            self.c = c

    def __init__(self, c):

        ### Do we need to change the dummy frame???
        dummy_frame = self.DummyFrame(c)
        leoFrame.LeoTree.__init__(self, dummy_frame)
            # Init the base class.
        assert self.c
        ###
            # assert not hasattr(self, 'treeWidget')
            # self.treeWidget = self
        assert not hasattr(self, 'tree_widget')
        self.tree_widget = None
            # A LeoMLTree set by CGui.createCursesTree.
        # Associating items with position and vnodes...
        self.item2positionDict = {}
        self.item2vnodeDict = {}
        self.position2itemDict = {}
        self.vnode2itemsDict = {} # values are lists of items.
        self.editWidgetsDict = {} # keys are native edit widgets, values are wrappers.
        # self.setConfigIvars()
        self.setEditPosition(None) # Set positions returned by LeoTree.editPosition()
        # Status flags...
        self.contracting = False
        self.expanding = False
        self.redrawing = False
        self.selecting = False
    #@+node:ekr.20170511104032.1: *3* CTree.Debugging & tracing
    def error(self, s):
        if not g.app.unitTesting:
            g.trace('LeoQtTree Error: %s' % (s), g.callers())

    def traceItem(self, item):
        if item:
            return 'item %s: %s' % (id(item), self.getItemText(item))
        else:
            return '<no item>'

    # def traceCallers(self):
        # if self.traceCallersFlag:
            # return g.callers(5, excludeCaller=True)
        # else:
            # return ''
    #@+node:ekr.20170511094217.1: *3* CTree.Drawing
    #@+node:ekr.20170511094217.3: *4* CTree.redraw & helpers
    def redraw(self, p=None, scroll=True, forceDraw=False):
        '''
        Redraw all visible nodes of the tree.
        Preserve the vertical scrolling unless scroll is True.
        '''
        if 1:
            return ###
        else:
            trace = False and not g.app.unitTesting
            verbose = False
            c = self.c
            if g.app.disable_redraw:
                if trace: g.trace('*** disabled', g.callers())
                return
            if self.busy():
                return g.trace('*** full_redraw: busy!', g.callers())
            if not p:
                p = c.currentPosition()
            elif c.hoistStack and p.h.startswith('@chapter') and p.hasChildren():
                # Make sure the current position is visible.
                # Part of fix of bug 875323: Hoist an @chapter node leaves a non-visible node selected.
                p = p.firstChild()
                if trace: g.trace('selecting', p.h)
                c.frame.tree.select(p)
                c.setCurrentPosition(p)
            else:
                c.setCurrentPosition(p)
            self.redrawCount += 1
            if trace: t1 = g.getTime()
            self.initData()
            self.nodeDrawCount = 0
            try:
                self.redrawing = True
                self.drawTopTree(p)
            finally:
                self.redrawing = False
            self.setItemForCurrentPosition(scroll=scroll)
            c.requestRedrawFlag = False
            if trace:
                if verbose:
                    theTime = g.timeSince(t1)
                    g.trace('** %s: scroll %5s drew %3s nodes in %s' % (
                        self.redrawCount, scroll, self.nodeDrawCount, theTime), g.callers())
                else:
                    g.trace('**', self.redrawCount, g.callers())
            return p # Return the position, which may have changed.
    # Compatibility

    full_redraw = redraw
    redraw_now = redraw
    #@+node:ekr.20170511094217.5: *5* CTree.declutter_node (not used)
    def declutter_node(self, c, p, item):
        """declutter_node - change the appearance of a node

        :param commander c: commander containing node
        :param position p: position of node
        :param QWidgetItem item: tree node widget item
        """
        pass
        # if self.declutter_patterns is None:
            # self.declutter_patterns = []
            # lines = c.config.getData("tree-declutter-patterns")
            # while lines:
                # line = lines.pop(0)
                # cmd, arg = line.split(None, 1)
                # if cmd == 'RULE':
                    # self.declutter_patterns.append((re.compile(arg), []))
                    # continue
                # self.declutter_patterns[-1][1].append((cmd, arg))

        # text = str(item.text(0)) if g.isPython3 else g.u(item.text(0))
        # new_icons = []
        # for pattern, cmds in self.declutter_patterns:
            # if pattern.match(text):

                # for cmd, arg in cmds:
                    # if cmd == 'REPLACE':
                        # text = pattern.sub(arg, text)
                        # item.setText(0, text)
                        # continue
                    # arg = c.styleSheetManager.expand_css_constants(arg).split()[0]
                    # if cmd == 'ICON':
                        # new_icons.append(arg)
                    # elif cmd == 'BG':
                        # item.setBackground(0, QtGui.QBrush(QtGui.QColor(arg)))
                    # elif cmd == 'FG':
                        # item.setForeground(0, QtGui.QBrush(QtGui.QColor(arg)))
                    # elif cmd == 'FONT':
                        # item.setFont(0, QtGui.QFont(arg))
                    # elif cmd == 'ITALIC':
                        # font = item.font(0)
                        # font.setItalic(bool(int(arg)))
                        # item.setFont(0, font)
                    # elif cmd == 'WEIGHT':
                        # arg = getattr(QtGui.QFont, arg, 75)
                        # font = item.font(0)
                        # font.setWeight(arg)
                        # item.setFont(0, font)
                    # elif cmd == 'PX':
                        # font = item.font(0)
                        # font.setPixelSize(int(arg))
                        # item.setFont(0, font)
                    # elif cmd == 'PT':
                        # font = item.font(0)
                        # font.setPointSize(int(arg))
                        # item.setFont(0, font)

        # com = c.editCommands
        # allIcons = com.getIconList(p)
        # icons = [i for i in allIcons if 'visualIcon' not in i]
        # if len(allIcons) != len(icons) or new_icons:
            # for icon in new_icons:
                # com.appendImageDictToList(
                    # icons, self.declutter_iconDir,
                    # g.app.gui.getImageImageFinder(icon), 2,
                    # on='vnode', visualIcon='1'
                # )
            # com.setIconList(p, icons, False)
    #@+node:ekr.20170511094217.6: *5* CTree.drawChildren
    def drawChildren(self, p, parent_item):
        '''Draw the children of p if they should be expanded.'''
        trace = False and not g.unitTesting
        # if trace: g.trace('children: %5s expanded: %5s %s childIndex: %s' % (
            # p.hasChildren(),p.isExpanded(),p.h,p._childIndex))
        if not p:
            return g.trace('can not happen: no p')
        if p.hasChildren():
            if p.isExpanded():
                if trace: g.trace('expanded', p, p._childIndex)
                self.expandItem(parent_item)
                child = p.firstChild()
                while child:
                    self.drawTree(child, parent_item)
                    child.moveToNext()
            else:
                # Draw the hidden children.
                child = p.firstChild()
                while child:
                    self.drawNode(child, parent_item)
                    child.moveToNext()
                self.contractItem(parent_item)
        else:
            self.contractItem(parent_item)
    #@+node:ekr.20170511094217.7: *5* CTree.drawNode
    def drawNode(self, p, parent_item):
        '''Draw the node p.'''
        trace = False
        self.nodeDrawCount += 1
        # Allocate the item.
        item = self.createTreeItem(p, parent_item)
        # Do this now, so self.isValidItem will be true in setItemIcon.
        self.rememberItem(p, item)
        # Set the headline and maybe the icon.
        self.setItemText(item, p.h)
        # if self.use_declutter:
            # self.declutter_node(self.c, p, item)
        # if p:
            # self.drawItemIcon(p, item)
        if trace: g.trace(self.traceItem(item))
        return item
    #@+node:ekr.20170511094217.8: *5* CTree.drawTopTree
    def drawTopTree(self, p):
        '''Draw the tree rooted at p.'''
        trace = False and not g.unitTesting
        c = self.c
        hPos, vPos = self.getScroll()
        self.clear()
        # Draw all top-level nodes and their visible descendants.
        if c.hoistStack:
            bunch = c.hoistStack[-1]
            p = bunch.p; h = p.h
            if len(c.hoistStack) == 1 and h.startswith('@chapter') and p.hasChildren():
                p = p.firstChild()
                while p:
                    self.drawTree(p)
                    p.moveToNext()
            else:
                self.drawTree(p)
        else:
            p = c.rootPosition()
            if trace: g.trace(p)
            while p:
                self.drawTree(p)
                p.moveToNext()
        # This method always retains previous scroll position.
        self.setHScroll(hPos)
        self.setVScroll(vPos)
        self.repaint()
    #@+node:ekr.20170511094217.9: *5* CTree.drawTree
    def drawTree(self, p, parent_item=None):
        if g.app.gui.isNullGui:
            return
        # Draw the (visible) parent node.
        item = self.drawNode(p, parent_item)
        # Draw all the visible children.
        self.drawChildren(p, parent_item=item)
    #@+node:ekr.20170511094217.10: *5* CTree.initData
    def initData(self):
        
        # g.trace('*****')
        self.item2positionDict = {}
        self.item2vnodeDict = {}
        self.position2itemDict = {}
        self.vnode2itemsDict = {}
        self.editWidgetsDict = {}
    #@+node:ekr.20170511094217.11: *5* CTree.rememberItem
    def rememberItem(self, p, item):

        trace = False and not g.unitTesting
        if trace: g.trace('id', id(item), p)
        v = p.v
        # Update position dicts.
        itemHash = self.itemHash(item)
        self.position2itemDict[p.key()] = item
        self.item2positionDict[itemHash] = p.copy() # was item
        # Update item2vnodeDict.
        self.item2vnodeDict[itemHash] = v # was item
        # Update vnode2itemsDict.
        d = self.vnode2itemsDict
        aList = d.get(v, [])
        if item in aList:
            g.trace('*** ERROR *** item already in list: %s, %s' % (item, aList))
        else:
            aList.append(item)
        d[v] = aList
    #@+node:ekr.20170511100356.1: *4* CTree.redraw_after...
    #@+node:ekr.20170511094217.14: *5* CTree.redraw_after_contract
    def redraw_after_contract(self, p=None):

        trace = False and not g.unitTesting
        if self.redrawing:
            return
        item = self.position2item(p)
        if item:
            if trace: g.trace('contracting item', item, p and p.h or '<no p>')
            self.contractItem(item)
        else:
            # This is not an error.
            # We may have contracted a node that was not, in fact, visible.
            if trace: g.trace('***full redraw', p and p.h or '<no p>')
            self.full_redraw(scroll=False)
    #@+node:ekr.20170511094217.15: *5* CTree.redraw_after_expand
    def redraw_after_expand(self, p=None):

        self.full_redraw(p, scroll=True)
    #@+node:ekr.20170511094217.16: *5* CTree.redraw_after_head_changed
    def redraw_after_head_changed(self):
        
        if not self.busy():
            p = self.c.p
            if p:
                for item in self.vnode2items(p.v):
                    if self.isValidItem(item):
                        self.setItemText(item, p.h)
            self.redraw_after_icons_changed()
    #@+node:ekr.20170511094217.17: *5* CTree.redraw_after_icons_changed
    def redraw_after_icons_changed(self):
        pass
        ### No icons to draw.
            # if self.busy(): return
            # self.redrawCount += 1 # To keep a unit test happy.
            # c = self.c
            # # Suppress call to setHeadString in onItemChanged!
            # self.redrawing = True
            # try:
                # self.getCurrentItem()
                # for p in c.rootPosition().self_and_siblings():
                    # # Updates icons in p and all visible descendants of p.
                    # self.updateVisibleIcons(p)
            # finally:
                # self.redrawing = False
    #@+node:ekr.20170511094217.18: *5* CTree.redraw_after_select
    # Important: this can not replace before/afterSelectHint.

    def redraw_after_select(self, p=None):
        '''Redraw the entire tree when an invisible node is selected.'''
        trace = False and not g.unitTesting
        if trace: g.trace('(LeoQtTree) busy? %s %s' % (
            self.busy(), p and p.h or '<no p>'), g.callers(4))
        # Prevent the selecting lockout from disabling the redraw.
        oldSelecting = self.selecting
        self.selecting = False
        try:
            if not self.busy():
                self.full_redraw(p, scroll=False)
        finally:
            self.selecting = oldSelecting
        # c.redraw_after_select calls tree.select indirectly.
        # Do not call it again here.
    #@+node:ekr.20170511094217.19: *4* CTree.repaint
    def repaint(self):
        '''Repaint the widget.'''
        # if self.tree_widget:
            # self.tree_widget.update()
       
    #@+node:ekr.20170511104533.1: *3* CTree.Event handlers (**LeoMLTree must generate these events)
    #@+node:ekr.20170511104533.10: *4* CTree.busy
    def busy(self):
        '''Return True (actually, a debugging string)
        if any lockout is set.'''
        trace = False
        table = (
            (self.contracting, 'contracting'),
            (self.expanding, 'expanding'),
            (self.redrawing, 'redrawing'),
            (self.selecting, 'selecting'))
        item = self.getCurrentItem()
        aList = []
        for ivar, kind in table:
            if ivar:
                aList.append(kind)
        kinds = ','.join(aList)
        if aList and trace:
            g.trace(self.traceItem(item), kinds, g.callers(4))
        return kinds # Return the string for debugging
    #@+node:ekr.20170511104533.12: *4* CTree.onHeadChanged
    # Tricky code: do not change without careful thought and testing.

    def onHeadChanged(self, p, undoType='Typing', s=None, e=None):
        '''Officially change a headline.'''
        trace = False and not g.unitTesting
        trace_hook = True
        verbose = False
        c = self.c; u = c.undoer
        if not p:
            if trace and verbose: g.trace('** no p')
            return
        item = self.getCurrentItem()
        if not item:
            if trace and verbose: g.trace('** no item')
            return
        if not e:
            e = self.getTreeEditorForItem(item)
        if not e:
            if trace and verbose: g.trace('(nativeTree) ** not editing')
            return
        s = g.u(e.text())
        self.closeEditorHelper(e, item)
        oldHead = p.h
        changed = s != oldHead
        if trace and trace_hook:
            g.trace('headkey1: changed %s' % (changed), g.callers())
        if g.doHook("headkey1", c=c, p=c.p, v=c.p, s=s, changed=changed):
            return
        if changed:
            # New in Leo 4.10.1.
            if trace: g.trace('(nativeTree) new', repr(s), 'old', repr(p.h))
            #@+<< truncate s if it has multiple lines >>
            #@+node:ekr.20170511104533.13: *5* << truncate s if it has multiple lines >>
            # Remove trailing newlines before warning of truncation.
            while s and s[-1] == '\n':
                s = s[: -1]
            # Warn if there are multiple lines.
            i = s.find('\n')
            if i > -1:
                s = s[: i]
                if s != oldHead:
                    g.warning("truncating headline to one line")
            limit = 1000
            if len(s) > limit:
                s = s[: limit]
                if s != oldHead:
                    g.warning("truncating headline to", limit, "characters")
            #@-<< truncate s if it has multiple lines >>
            p.initHeadString(s)
            item.setText(0, s) # Required to avoid full redraw.
            undoData = u.beforeChangeNodeContents(p, oldHead=oldHead)
            if not c.changed: c.setChanged(True)
            # New in Leo 4.4.5: we must recolor the body because
            # the headline may contain directives.
            c.frame.body.recolor(p, incremental=True)
            dirtyVnodeList = p.setDirty()
            u.afterChangeNodeContents(p, undoType, undoData,
                dirtyVnodeList=dirtyVnodeList, inHead=True) # 2013/08/26.
        g.doHook("headkey2", c=c, p=c.p, v=c.p, s=s, changed=changed)
        # This is a crucial shortcut.
        if g.unitTesting: return
        if changed:
            self.redraw_after_head_changed()
        # Don't do this: it interferes with clicks, and is not needed.
            # if self.stayInTree:
                # c.treeWantsFocus()
            # else:
                # c.bodyWantsFocus()
        p.v.contentModified()
        c.outerUpdate()
    #@+node:ekr.20170511104533.18: *4* CTree.onTreeSelect
    def onTreeSelect(self):
        '''Select the proper position when a tree node is selected.'''
        trace = False and not g.unitTesting
        if self.busy(): return
        c = self.c
        item = self.getCurrentItem()
        p = self.item2position(item)
        if p:
            # Important: do not set lockouts here.
            # Only methods that actually generate events should set lockouts.
            if trace: g.trace(self.traceItem(item))
            self.select(p)
                # This is a call to LeoTree.select(!!)
                # Calls before/afterSelectHint.
        else:
            self.error('no p for item: %s' % item)
        c.outerUpdate()
    #@+node:ekr.20170511104533.19: *4* CTree.OnPopup & allies
    def OnPopup(self, p, event):
        """Handle right-clicks in the outline.

        This is *not* an event handler: it is called from other event handlers."""
        # Note: "headrclick" hooks handled by VNode callback routine.
        if event:
            c = self.c
            c.setLog()
            if not g.doHook("create-popup-menu", c=c, p=p, v=p, event=event):
                self.createPopupMenu(event)
            if not g.doHook("enable-popup-menu-items", c=c, p=p, v=p, event=event):
                self.enablePopupMenuItems(p, event)
            if not g.doHook("show-popup-menu", c=c, p=p, v=p, event=event):
                self.showPopupMenu(event)
        return "break"
    #@+node:ekr.20170511104533.20: *5* CTree.OnPopupFocusLost
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
    #@+node:ekr.20170511104533.21: *5* CTree.createPopupMenu
    def createPopupMenu(self, event):
        '''This might be a placeholder for plugins.  Or not :-)'''
    #@+node:ekr.20170511104533.22: *5* CTree.enablePopupMenuItems
    def enablePopupMenuItems(self, v, event):
        """Enable and disable items in the popup menu."""
    #@+node:ekr.20170511104533.23: *5* CTree.showPopupMenu
    def showPopupMenu(self, event):
        """Show a popup menu."""
    #@+node:ekr.20170511101300.1: *3* CTree.Items

    #@+node:ekr.20170511101300.2: *4*  CTree.item dict getters
    def itemHash(self, item):
        return '%s at %s' % (repr(item), str(id(item)))

    def item2position(self, item):
        itemHash = self.itemHash(item)
        p = self.item2positionDict.get(itemHash) # was item
        # g.trace(item,p.h)
        return p

    def item2vnode(self, item):
        itemHash = self.itemHash(item)
        return self.item2vnodeDict.get(itemHash) # was item

    def position2item(self, p):
        item = self.position2itemDict.get(p.key())
        return item

    def vnode2items(self, v):
        return self.vnode2itemsDict.get(v, [])

    def isValidItem(self, item):
        itemHash = self.itemHash(item)
        return itemHash in self.item2vnodeDict # was item.
    #@+node:ekr.20170511101300.3: *4* CTree.childIndexOfItem
    def childIndexOfItem(self, item):
        parent = item and item.parent()
        if parent:
            n = parent.indexOfChild(item)
        else:
            w = self.tree_widget
            n = w.indexOfTopLevelItem(item)
        return n
    #@+node:ekr.20170511101300.4: *4* CTree.childItems
    def childItems(self, parent_item):
        '''Return the list of child items of the parent item,
        or the top-level items if parent_item is None.'''
        if parent_item:
            n = parent_item.childCount()
            items = [parent_item.child(z) for z in range(n)]
        else:
            w = self.tree_widget
            n = w.topLevelItemCount()
            items = [w.topLevelItem(z) for z in range(n)]
        return items
    #@+node:ekr.20170511101300.5: *4* CTree.closeEditorHelper
    def closeEditorHelper(self, e, item):
        'End editing of the underlying QLineEdit widget for the headline.' ''
        w = self.tree_widget
        
        if e:
            ### w.closeEditor(e, QtWidgets.QAbstractItemDelegate.NoHint)
            try:
                # work around https://bugs.launchpad.net/leo-editor/+bug/1041906
                # underlying C/C++ object has been deleted
                w.setItemWidget(item, 0, None)
                    # Make sure e is never referenced again.
                w.setCurrentItem(item)
            except RuntimeError:
                if 1: # Testing.
                    g.es_exception()
                else:
                    # Recover silently even if there is a problem.
                    pass
    #@+node:ekr.20170511101300.6: *4* CTree.connectEditorWidget & helper
    def connectEditorWidget(self, e, item):
        if not e:
            return g.trace('can not happen: no e')
        # Hook up the widget.
        wrapper = self.getWrapper(e, item)

        def editingFinishedCallback(e=e, item=item, self=self, wrapper=wrapper):
            # g.trace(wrapper,g.callers(5))
            c = self.c
            w = self.tree_widget
            self.onHeadChanged(p=c.p, e=e)
            w.setCurrentItem(item)

        e.editingFinished.connect(editingFinishedCallback)
        return wrapper # 2011/02/12
    #@+node:ekr.20170511101300.7: *4* CTree.contractItem & expandItem
    def contractItem(self, item):
        # g.trace(g.callers(4))
        if self.tree_widget:
            self.tree_widget.collapseItem(item)

    def expandItem(self, item):
        # g.trace(g.callers(4))
        if self.tree_widget:
            self.tree_widget.expandItem(item)
    #@+node:ekr.20170511101300.8: *4* CTree.createTreeEditorForItem
    def createTreeEditorForItem(self, item):
        trace = False and not g.unitTesting
        w = self.tree_widget
        w.setCurrentItem(item) # Must do this first.
        # if self.use_declutter:
            # item.setText(0, item._real_text)
        w.editItem(item)
        e = w.itemWidget(item, 0)
        e.setObjectName('headline')
        wrapper = self.connectEditorWidget(e, item)
        if trace: g.trace(e, wrapper)
        self.sizeTreeEditor(self.c, e)
        return e, wrapper
    #@+node:ekr.20170511101300.9: *4* CTree.createTreeItem
    def createTreeItem(self, p, parent_item):
        trace = False and not g.unitTesting
        c = self.c
        ###
            # w = self.tree_widget
            # itemOrTree = parent_item or w
            # item = QtWidgets.QTreeWidgetItem(itemOrTree)
            # item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        item = g.NullObject() ###
        if trace: g.trace(id(item), p.h, g.callers(4))
        try:
            g.visit_tree_item(c, p, item)
        except leoPlugins.TryNext:
            pass
        return item
    #@+node:ekr.20170511101300.11: *4* CTree.getCurrentItem
    def getCurrentItem(self):
        w = self.tree_widget
        return w and w.currentItem
    #@+node:ekr.20170511101300.12: *4* CTree.getItemText
    def getItemText(self, item):
        '''Return the text of the item.'''
        if item:
            return g.u(item.text(0))
        else:
            return '<no item>'
    #@+node:ekr.20170511101300.13: *4* CTree.getParentItem
    def getParentItem(self, item):
        return item and item.parent()
    #@+node:ekr.20170511101300.14: *4* CTree.getSelectedItems
    def getSelectedItems(self):
        w = self.tree_widget
        return w.selectedItems()
    #@+node:ekr.20170511101300.15: *4* CTree.getTreeEditorForItem
    def getTreeEditorForItem(self, item):
        '''Return the edit widget if it exists.
        Do *not* create one if it does not exist.'''
        trace = False and not g.unitTesting
        w = self.tree_widget
        e = w.itemWidget(item, 0)
        if trace and e: g.trace(e.__class__.__name__)
        return e
    #@+node:ekr.20170511101300.16: *4* CTree.getWrapper
    def getWrapper(self, e, item):
        '''Return headlineWrapper that wraps e (a QLineEdit).'''
        trace = False and not g.unitTesting
        c = self.c
        if e:
            wrapper = self.editWidgetsDict.get(e)
            if wrapper:
                pass # g.trace('old wrapper',e,wrapper)
            else:
                if item:
                    # 2011/02/12: item can be None.
                    wrapper = CursesHeadlineWrapper(c, item, name='head', widget=e)
                    if trace: g.trace('new wrapper', e, wrapper)
                    self.editWidgetsDict[e] = wrapper
                else:
                    if trace: g.trace('no item and no wrapper',
                        e, self.editWidgetsDict)
            return wrapper
        else:
            g.trace('no e')
            return None
    #@+node:ekr.20170511101300.17: *4* CTree.nthChildItem
    def nthChildItem(self, n, parent_item):
        children = self.childItems(parent_item)
        if n < len(children):
            item = children[n]
        else:
            # This is **not* an error.
            # It simply means that we need to redraw the tree.
            item = None
        return item
    #@+node:ekr.20170511101300.18: *4* CTree.scrollToItem
    def scrollToItem(self, item):
        w = self.tree_widget
        # g.trace(self.traceItem(item))
        hPos, vPos = self.getScroll()
        w.scrollToItem(item, w.EnsureVisible)
            # Fix #265: Erratic scrolling bug.
            # w.PositionAtCenter causes unwanted scrolling.
        self.setHScroll(0)
            # Necessary
    #@+node:ekr.20170511101300.19: *4* CTree.setCurrentItemHelper
    def setCurrentItemHelper(self, item):
        w = self.tree_widget
        w.setCurrentItem(item)
    #@+node:ekr.20170511101300.20: *4* CTree.setItemText
    def setItemText(self, item, s):
        if item:
            item.setText(0, s)
            # if self.use_declutter:
                # item._real_text = s
    #@+node:ekr.20170511101300.21: *4* CTree.sizeTreeEditor
    @staticmethod
    def sizeTreeEditor(c, editor):
        """Size a QLineEdit in a tree headline so scrolling occurs"""
        # space available in tree widget
        space = c.frame.tree.tree_widget.size().width()
        # left hand edge of editor within tree widget
        used = editor.geometry().x() + 4  # + 4 for edit cursor
        # limit width to available space
        editor.resize(space - used, editor.size().height())
    #@+node:ekr.20170511104121.1: *3* CTree.Scroll bars
    #@+node:ekr.20170511104121.2: *4* Ctree.getScroll
    def getScroll(self):
        '''Return the hPos,vPos for the tree's scrollbars.'''
        return 0, 0
        # w = self.tree_widget
        # hScroll = w.horizontalScrollBar()
        # vScroll = w.verticalScrollBar()
        # hPos = hScroll.sliderPosition()
        # vPos = vScroll.sliderPosition()
        # return hPos, vPos
    #@+node:ekr.20170511104121.3: *4* Ctree.scrollDelegate
    # def scrollDelegate(self, kind):
        # '''Scroll a QTreeWidget up or down or right or left.
        # kind is in ('down-line','down-page','up-line','up-page', 'right', 'left')
        # '''
        # c = self.c; w = self.tree_widget
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
    #@+node:ekr.20170511104121.4: *4* Ctree.setH/VScroll
    def setHScroll(self, hPos):
        pass
        # w = self.tree_widget
        # hScroll = w.horizontalScrollBar()
        # hScroll.setValue(hPos)

    def setVScroll(self, vPos):
        pass
        # w = self.tree_widget
        # vScroll = w.verticalScrollBar()
        # vScroll.setValue(vPos)
    #@+node:ekr.20170511105355.1: *3* CTree.Selecting & editing
    #@+node:ekr.20170511105355.2: *4* CTree.afterSelectHint
    def afterSelectHint(self, p, old_p):
        trace = False and not g.unitTesting
        c = self.c
        self.selecting = False
        if self.busy():
            self.error('afterSelectHint busy!: %s' % self.busy())
        if not p:
            return self.error('no p')
        if p != c.p:
            if trace: self.error(
                '(afterSelectHint) p != c.p\np:   %s\nc.p: %s\n' % (
                repr(p), repr(c.currentPosition())))
            p = c.p
        # if trace: g.trace(c.p.h,g.callers())
        # We don't redraw during unit testing: an important speedup.
        if c.expandAllAncestors(p) and not g.unitTesting:
            if trace: g.trace('***self.full_redraw')
            self.full_redraw(p)
        else:
            if trace: g.trace('*** c.outerUpdate')
            c.outerUpdate() # Bring the tree up to date.
            self.setItemForCurrentPosition(scroll=False)
    #@+node:ekr.20170511105355.3: *4* CTree.beforeSelectHint
    def beforeSelectHint(self, p, old_p):
        trace = False and not g.unitTesting
        if self.busy(): return
        c = self.c
        if trace: g.trace(p and p.h, c.p.h)
        # Disable onTextChanged.
        self.selecting = True
        self.prev_v = c.p.v
    #@+node:ekr.20170511105355.4: *4* CTree.edit_widget
    def edit_widget(self, p):
        """Returns the edit widget for position p."""
        return CursesTextWrapper(c=self.c, name='head', w=None)
        ### Old code.
            # trace = False and not g.unitTesting
            # verbose = False
            # item = self.position2item(p)
            # if item:
                # e = self.getTreeEditorForItem(item)
                # if e:
                    # # Create a wrapper widget for Leo's core.
                    # w = self.getWrapper(e, item)
                    # if trace: g.trace(w, p and p.h)
                    # return w
                # else:
                    # # This is not an error
                    # # But warning: calling this method twice might not work!
                    # if trace and verbose: g.trace('no e for %s' % (p))
                    # return None
            # else:
                # if trace and verbose: self.error('no item for %s' % (p))
                # return None
    #@+node:ekr.20170511095353.1: *4* CTree.editLabel & helper
    def editLabel(self, p, selectAll=False, selection=None):
        """Start editing p's headline."""
        trace = False and not g.unitTesting
        if self.busy():
            if trace: g.trace('busy')
            return
        c = self.c
        c.outerUpdate()
            # Do any scheduled redraw.
            # This won't do anything in the new redraw scheme.
        item = self.position2item(p)
        if item:
            # if self.use_declutter:
                # item.setText(0, item._real_text)
            e, wrapper = self.editLabelHelper(item, selectAll, selection)
        else:
            e, wrapper = None, None
            self.error('no item for %s' % p)
        if trace: g.trace('p: %s e: %s' % (p and p.h, e))
        if e:
            self.sizeTreeEditor(c, e)
            # A nice hack: just set the focus request.
            c.requestedFocusWidget = e
        return e, wrapper
    #@+node:ekr.20170511095244.22: *5* CTree.editLabelHelper
    def editLabelHelper(self, item, selectAll=False, selection=None):
        '''
        Help nativeTree.editLabel do gui-specific stuff.
        '''
        c, vc = self.c, self.c.vimCommands
        w = self.tree_widget
        w.setCurrentItem(item)
            # Must do this first.
            # This generates a call to onTreeSelect.
        w.editItem(item)
            # Generates focus-in event that tree doesn't report.
        e = w.itemWidget(item, 0) # A QLineEdit.
        if e:
            s = e.text(); len_s = len(s)
            if s == 'newHeadline': selectAll = True
            if selection:
                # pylint: disable=unpacking-non-sequence
                # Fix bug https://groups.google.com/d/msg/leo-editor/RAzVPihqmkI/-tgTQw0-LtwJ
                # Note: negative lengths are allowed.
                i, j, ins = selection
                if ins is None:
                    start, n = i, abs(i - j)
                    # This case doesn't happen for searches.
                elif ins == j:
                    start, n = i, j - i
                else:
                    start = start, n = j, i - j
                # g.trace('i',i,'j',j,'ins',ins,'-->start',start,'n',n)
            elif selectAll: start, n, ins = 0, len_s, len_s
            else: start, n, ins = len_s, 0, len_s
            e.setObjectName('headline')
            e.setSelection(start, n)
            # e.setCursorPosition(ins) # Does not work.
            e.setFocus()
            wrapper = self.connectEditorWidget(e, item) # Hook up the widget.
            if vc and c.vim_mode: #  and selectAll
                # For now, *always* enter insert mode.
                if vc.is_text_wrapper(wrapper):
                    vc.begin_insert_mode(w=wrapper)
                else:
                    g.trace('not a text widget!', wrapper)
        return e, wrapper
    #@+node:ekr.20170511105355.6: *4* CTree.editPosition
    def editPosition(self):
        c = self.c; p = c.currentPosition()
        ew = self.edit_widget(p)
        return p if ew else None
    #@+node:ekr.20170511105355.7: *4* CTree.endEditLabel
    def endEditLabel(self):
        '''Override LeoTree.endEditLabel.

        End editing of the presently-selected headline.'''
        c = self.c; p = c.currentPosition()
        self.onHeadChanged(p)
    #@+node:ekr.20170511105355.8: *4* CTree.getSelectedPositions
    def getSelectedPositions(self):
        items = self.getSelectedItems()
        pl = leoNodes.PosList(self.item2position(it) for it in items)
        return pl
    #@+node:ekr.20170511105355.9: *4* CTree.setHeadline
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
        if e:
            if trace: g.trace('e', s)
            e.setAllText(s)
        else:
            item = self.position2item(p)
            if item:
                if trace: g.trace('item', s)
                self.setItemText(item, s)
            else:
                if trace: g.trace('*** failed. no item for %s' % p.h)
    #@+node:ekr.20170511105355.10: *4* CTree.setItemForCurrentPosition
    def setItemForCurrentPosition(self, scroll=True):
        '''Select the item for c.p'''
        trace = False and not g.unitTesting
        verbose = True
        c = self.c; p = c.currentPosition()
        if self.busy():
            if trace and verbose: g.trace('** busy')
            return None
        if not p:
            if trace and verbose: g.trace('** no p')
            return None
        item = self.position2item(p)
        if not item:
            # This is not necessarily an error.
            # We often attempt to select an item before redrawing it.
            if trace and verbose:
                g.trace('** no item for', p)
                g.trace(g.callers())
            return None
        item2 = self.getCurrentItem()
        if item == item2:
            if trace and verbose: g.trace('no change', self.traceItem(item), p.h)
            if scroll:
                self.scrollToItem(item)
        else:
            try:
                self.selecting = True
                # This generates gui events, so we must use a lockout.
                if trace and verbose: g.trace('setCurrentItem', self.traceItem(item), p.h)
                self.setCurrentItemHelper(item)
                    # Just calls self.setCurrentItem(item)
                if scroll:
                    if trace: g.trace(self.traceItem(item))
                    self.scrollToItem(item)
            finally:
                self.selecting = False
        # if trace: g.trace('item',repr(item))
        if not item: g.trace('*** no item')
        return item
    #@+node:ekr.20170511100548.1: *3* CTree.Unused
    #@+node:ekr.20170511104916.1: *4* Unused drawing code
    #@+node:ekr.20170511094217.2: *5* CTree.clear (do-nothing)
    def clear(self):
        '''Clear all widgets in the tree.'''
        # g.trace('=====', g.callers())
        # w = self.tree_widget
        # w.clear()
    #@+node:ekr.20170511094217.4: *5* CTree.clear_visual_icons
    def clear_visual_icons(self, tag, keywords):
        """clear_visual_icons - remove 'declutter' icons before save

        this method must return None to tell Leo to continue normal processing

        :param str tag: 'save1'
        :param dict keywords: Leo hook keywords
        """
        return None
        ###
            # if not self.use_declutter:
                # return None
            # c = keywords['c']
            # if c != self.c:
                # return None
            # if c.config.getBool('tree-declutter', default=False):
                # com = c.editCommands
                # for nd in c.all_unique_positions():
                    # icons = [i for i in com.getIconList(nd) if 'visualIcon' not in i]
                    # com.setIconList(nd, icons, False)
            # self.declutter_update = True
            # return None
    #@+node:ekr.20170511094126.1: *5* CTree.drawIcon (Used?)
    def drawIcon(self, p):
        
        g.trace('=====', g.callers())
    #@+node:ekr.20170511094126.6: *5* CTree.scrollTo (Used?)
    def scrollTo(self, p):
        g.trace('=====', g.callers())


    #@+node:ekr.20170511094217.12: *5* CTree.update_appearance (not used)
    def update_appearance(self, tag, keywords):
        """clear_visual_icons - update appearance, but can't call
        self.full_redraw() now, so just set a flag to do it on idle.

        :param str tag: 'headkey2'
        :param dict keywords: Leo hook keywords
        """
        return None
        ###
            # if not self.use_declutter:
                # return None
            # c = keywords['c']
            # if c != self.c:
                # return None
            # self.declutter_update = True
            # return None
    #@+node:ekr.20170511094217.13: *5* CTree.update_appearance_idle (not used)
    def update_appearance_idle(self, tag, keywords):
        """clear_visual_icons - update appearance now we're safely out of
        the redraw loop.

        :param str tag: 'idle'
        :param dict keywords: Leo hook keywords
        """
        return None
        ###
            # if not self.use_declutter:
                # return None
            # c = keywords['c']
            # if c != self.c:
                # return None
        
            # if isinstance(QtWidgets.QApplication.focusWidget(), QtWidgets.QLineEdit):
                # # when search results are found in headlines headkey2 fires
                # # (on the second search hit in a headline), and full_redraw()
                # # below takes the headline out of edit mode, and Leo crashes,
                # # probably because the find code didn't expect to leave edit
                # # mode.  So don't update when a QLineEdit has focus
                # return None
        
            # if self.declutter_update:
                # self.declutter_update = False
                # self.full_redraw(scroll=False)
            # return None
    #@+node:ekr.20170511104827.1: *4* Unused event handlers
    ### Some of these may be needed.
    #@+node:ekr.20170511104533.2: *5* CTree.Click Box
    #@+node:ekr.20170511104533.3: *6* CTree.onClickBoxClick
    # def onClickBoxClick(self, event, p=None):
        # if self.busy(): return
        # c = self.c
        # g.doHook("boxclick1", c=c, p=p, v=p, event=event)
        # g.doHook("boxclick2", c=c, p=p, v=p, event=event)
        # c.outerUpdate()
    #@+node:ekr.20170511104533.4: *6* CTree.onClickBoxRightClick
    # def onClickBoxRightClick(self, event, p=None):
        # if self.busy(): return
        # c = self.c
        # g.doHook("boxrclick1", c=c, p=p, v=p, event=event)
        # g.doHook("boxrclick2", c=c, p=p, v=p, event=event)
        # c.outerUpdate()
    #@+node:ekr.20170511104533.5: *6* CTree.onPlusBoxRightClick
    # def onPlusBoxRightClick(self, event, p=None):
        # if self.busy(): return
        # c = self.c
        # g.doHook('rclick-popup', c=c, p=p, event=event, context_menu='plusbox')
        # c.outerUpdate()
    #@+node:ekr.20170511104533.6: *5* CTree.Icon Box
    #@+node:ekr.20170511104533.7: *6* CTree.onIconBoxClick
    # def onIconBoxClick(self, event, p=None):
        # if self.busy(): return
        # c = self.c
        # g.doHook("iconclick1", c=c, p=p, v=p, event=event)
        # g.doHook("iconclick2", c=c, p=p, v=p, event=event)
        # c.outerUpdate()
    #@+node:ekr.20170511104533.8: *6* CTree.onIconBoxRightClick
    # def onIconBoxRightClick(self, event, p=None):
        # """Handle a right click in any outline widget."""
        # if self.busy(): return
        # c = self.c
        # g.doHook("iconrclick1", c=c, p=p, v=p, event=event)
        # g.doHook("iconrclick2", c=c, p=p, v=p, event=event)
        # c.outerUpdate()
    #@+node:ekr.20170511104533.9: *6* CTree.onIconBoxDoubleClick
    # def onIconBoxDoubleClick(self, event, p=None):
        # if self.busy(): return
        # c = self.c
        # if not p: p = c.p
        # if not g.doHook("icondclick1", c=c, p=p, v=p, event=event):
            # self.endEditLabel()
            # self.OnIconDoubleClick(p) # Call the method in the base class.
        # g.doHook("icondclick2", c=c, p=p, v=p, event=event)
        # c.outerUpdate()
    #@+node:ekr.20170511104533.11: *5* CTree.onContextMenu
    # def onContextMenu(self, point):
        # c = self.c
        # w = self.tree_widget
        # handlers = g.tree_popup_handlers
        # menu = QtWidgets.QMenu()
        # menuPos = w.mapToGlobal(point)
        # if not handlers:
            # menu.addAction("No popup handlers")
        # p = c.p.copy()
        # done = set()
        # for h in handlers:
            # # every handler has to add it's QActions by itself
            # if h in done:
                # # do not run the same handler twice
                # continue
            # h(c, p, menu)
        # menu.popup(menuPos)
        # self._contextmenu = menu
    #@+node:ekr.20170511104533.14: *5* CTree.onItemClicked
    # def onItemClicked(self, item, col, auto_edit=False):
        # '''Handle a click in a BaseNativeTree widget item.'''
        # # This is called after an item is selected.
        # trace = False and not g.unitTesting
        # if self.busy(): return
        # c = self.c
        # # if trace: g.trace(self.traceItem(item),g.callers(4))
        # try:
            # self.selecting = True
            # p = self.item2position(item)
            # auto_edit = self.prev_v == p.v
            # if p:
                # self.prev_v = p.v
                # event = None
                # mods = g.app.gui.qtApp.keyboardModifiers()
                # # isCtrl = bool(mods & QtConst.ControlModifier)
                # if trace: g.trace('auto_edit', auto_edit, 'ctrl', isCtrl, p.h)
                # # We could also add support for QtConst.ShiftModifier, QtConst.AltModifier	& QtConst.MetaModifier.
                # if isCtrl:
                    # if g.doHook("iconctrlclick1", c=c, p=p, v=p, event=event) is None:
                        # c.frame.tree.OnIconCtrlClick(p) # Call the base class method.
                    # g.doHook("iconctrlclick2", c=c, p=p, v=p, event=event)
                # else:
                    # # 2014/02/21: generate headclick1/2 instead of iconclick1/2
                    # g.doHook("headclick1", c=c, p=p, v=p, event=event)
                    # g.doHook("headclick2", c=c, p=p, v=p, event=event)
            # else:
                # auto_edit = None
                # g.trace('*** no p')
            # # 2011/05/27: click here is like ctrl-g.
            # c.k.keyboardQuit(setFocus=False)
            # c.treeWantsFocus() # 2011/05/08: Focus must stay in the tree!
            # c.outerUpdate()
            # # 2011/06/01: A second *single* click on a selected node
            # # enters editing state.
            # if auto_edit and self.auto_edit:
                # e, wrapper = self.createTreeEditorForItem(item)
            # # 2014/10/26: Reset find vars.
            # c.findCommands.reset_state_ivars()
        # finally:
            # self.selecting = False
    #@+node:ekr.20170511104533.15: *5* CTree.onItemCollapsed
    # def onItemCollapsed(self, item):
        # trace = False
        # if self.busy(): return
        # c = self.c
        # if trace: g.trace(self.traceItem(item))
        # p = self.item2position(item)
        # if p:
            # # Important: do not set lockouts here.
            # # Only methods that actually generate events should set lockouts.
            # p.contract()
            # if p.isCloned():
                # self.select(p) # Calls before/afterSelectHint.
                # # 2010/02/04: Keep the expansion bits of all tree nodes in sync.
                # self.full_redraw(scroll=False)
            # else:
                # self.select(p) # Calls before/afterSelectHint.
        # else:
            # self.error('no p')
        # c.outerUpdate()
    #@+node:ekr.20170511104533.16: *5* CTree.onItemDoubleClicked
    # def onItemDoubleClicked(self, item, col):
        # '''Handle a double click in a BaseNativeTree widget item.'''
        # trace = False and not g.unitTesting
        # if self.busy(): return
        # c = self.c
        # if trace: g.trace(col, self.traceItem(item))
        # try:
            # self.selecting = True
            # e, wrapper = self.createTreeEditorForItem(item)
            # if not e:
                # g.trace('*** no e')
            # p = self.item2position(item)
        # # 2011/07/28: End the lockout here, not at the end.
        # finally:
            # self.selecting = False
        # if p:
            # # 2014/02/21: generate headddlick1/2 instead of icondclick1/2.
            # event = None
            # if g.doHook("headdclick1", c=c, p=p, v=p, event=event) is None:
                # c.frame.tree.OnIconDoubleClick(p) # Call the base class method.
            # g.doHook("headclick2", c=c, p=p, v=p, event=event)
        # else:
            # g.trace('*** no p')
        # c.outerUpdate()
    #@+node:ekr.20170511104533.17: *5* CTree.onItemExpanded
    # def onItemExpanded(self, item):
        # '''Handle and tree-expansion event.'''
        # trace = False
        # if self.busy(): return
        # c = self.c
        # if trace: g.trace(self.traceItem(item))
        # p = self.item2position(item)
        # if p:
            # # Important: do not set lockouts here.
            # # Only methods that actually generate events should set lockouts.
            # if not p.isExpanded():
                # p.expand()
                # self.select(p) # Calls before/afterSelectHint.
                # # Important: setting scroll=False here has no effect
                # # when a keystroke causes the expansion, but is a
                # # *big* improvement when clicking the outline.
                # self.full_redraw(scroll=False)
            # else:
                # self.select(p)
        # else:
            # self.error('no p')
        # c.outerUpdate()
    #@-others
#@+node:ekr.20170507194035.1: ** class LeoForm (npyscreen.Form)
class LeoForm (npyscreen.Form):
    
    OK_BUTTON_TEXT = 'Quit Leo'
#@+node:edward.20170428174322.1: ** class LeoKeyEvent (object)
class LeoKeyEvent(object):
    '''A gui-independent wrapper for gui events.'''
    #@+others
    #@+node:edward.20170428174322.2: *3* LeoKeyEvent.__init__
    def __init__(self, c, char, event, shortcut, w,
        x=None,
        y=None,
        x_root=None,
        y_root=None,
    ):
        '''Ctor for LeoKeyEvent class.'''
        trace = True
        assert not g.isStroke(shortcut), g.callers()
        stroke = g.KeyStroke(shortcut) if shortcut else None
        if trace: g.trace('LeoKeyEvent: stroke', stroke)
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
    #@+node:edward.20170428174322.3: *3* LeoKeyEvent.__repr__
    def __repr__(self):
        return 'LeoKeyEvent: stroke: %s, char: %s, w: %s' % (
            repr(self.stroke), repr(self.char), repr(self.w))
    #@+node:edward.20170428174322.4: *3* LeoKeyEvent.get & __getitem__
    def get(self, attr):
        '''Compatibility with g.bunch: return an attr.'''
        return getattr(self, attr, None)

    def __getitem__(self, attr):
        '''Compatibility with g.bunch: return an attr.'''
        return getattr(self, attr, None)
    #@+node:edward.20170428174322.5: *3* LeoKeyEvent.type
    def type(self):
        return 'LeoKeyEvent'
    #@-others
#@+node:ekr.20170510092721.1: ** class LeoMiniBuffer (npyscreen.Textfield)
class LeoMiniBuffer(npyscreen.Textfield):
    '''An npyscreen class representing Leo's minibuffer, with binding.''' 
    
    def __init__(self, *args, **kwargs):
        super(LeoMiniBuffer, self).__init__(*args, **kwargs)
        self.leo_c = None # Set later
        self.set_handlers()

    #@+others
    #@+node:ekr.20170510172335.1: *3* LeoMiniBuffer.Handlers
    #@+node:ekr.20170510095136.2: *4* LeoMiniBuffer.h_cursor_beginning
    def h_cursor_beginning(self, ch):

        #g.trace('LeoMiniBuffer', repr(ch))
        self.cursor_position = 0
    #@+node:ekr.20170510095136.3: *4* LeoMiniBuffer.h_cursor_end
    def h_cursor_end(self, ch):
        
        # g.trace('LeoMiniBuffer', repr(ch))
        self.cursor_position = len(self.value)
    #@+node:ekr.20170510095136.4: *4* LeoMiniBuffer.h_cursor_left
    def h_cursor_left(self, ch):
        
        # g.trace('LeoMiniBuffer', repr(ch))
        self.cursor_position = max(0, self.cursor_position -1)
    #@+node:ekr.20170510095136.5: *4* LeoMiniBuffer.h_cursor_right
    def h_cursor_right(self, ch):

        # g.trace('LeoMiniBuffer', repr(ch))
        self.cursor_position = min(len(self.value), self.cursor_position+1)


    #@+node:ekr.20170510095136.6: *4* LeoMiniBuffer.h_delete_left
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
    #@+node:ekr.20170510095136.7: *4* LeoMiniBuffer.h_insert
    def h_insert(self, ch):

        # g.trace('LeoMiniBuffer', ch, self.value)
        n = self.cursor_position + 1
        s = self.value
        self.value = s[:n] + chr(ch) + s[n:]
        self.cursor_position += 1
    #@+node:ekr.20170510100003.1: *4* LeoMiniBuffer.h_return (executes command)
    def h_return (self, ch):
        '''
        Handle the return key in the minibuffer.
        Send the contents to k.masterKeyHandler.
        '''
        c = self.leo_c
        # g.trace('LeoMiniBuffer', repr(ch), repr(self.value))
        c.k.masterCommand(
            commandName=self.value.strip(),
            event=LeoKeyEvent(c,char='',event='',shortcut='',w=self),
            func=None,
            stroke=None,
        )
    #@+node:ekr.20170510094104.1: *4* LeoMiniBuffer.set_handlers
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
#@+node:ekr.20170506035146.1: ** class LeoMLTree (npyscreen.MLTree)
class LeoMLTree(npyscreen.MLTree):

    # pylint: disable=used-before-assignment
    _contained_widgets = LeoTreeLine
    continuation_line = "- more -" # value of contination line.
    
    # def __init__ (self, *args, **kwargs):
        # super(LeoMLTree, self).__init__(*args, **kwargs
        
    # Note: The startup sequence sets leo_c and value property/ivar.
           
    #@+others
    #@+node:ekr.20170510171826.1: *3* LeoMLTree.Entries
    #@+node:ekr.20170506044733.6: *4* LeoMLTree.delete_line
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
            p.doDelete()
            self.values.clear_cache()
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
    #@+node:ekr.20170507171518.1: *4* LeoMLTree.dump_code/values/widgets
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
    #@+node:ekr.20170506044733.4: *4* LeoMLTree.edit_headline (done)
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
            ### active_line.set_leo_headline(active_line.value)
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
    #@+node:ekr.20170514065422.1: *4* LeoMLTree.intraFileDrop
    def intraFileDrop(self, fn, p1, p2):
        pass
    #@+node:ekr.20170506044733.2: *4* LeoMLTree.new_mltree_node
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
    #@+node:ekr.20170506044733.5: *4* LeoMLTree.insert_line (done)
    def insert_line(self):
        
        trace = False
        n = 0 if self.cursor_line is None else self.cursor_line
        if trace: g.trace('line: %r', n)
            # if trace_values: self.dump_values()
        if native:
            data = self.values[n] # data is a LeoTreeData
            if 0:
                c = self.leo_c
                c.insertHeadline()
                    # Calls LeoQtTree ?????
            else:
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
    #@+node:ekr.20170514101636.1: *4* LeoMLTree.set_is_line_cursor (not used)
    # def set_is_line_cursor(self, line, value):
        # # only defined in MultiLine
        # line.highlight = value
    #@+node:ekr.20170506045346.1: *3* LeoMLTree.Handlers
    # These insert or delete entire outline nodes.
    #@+node:ekr.20170516055435.4: *4* LeoMLTree.h_collapse_all (done)
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

    #@+node:ekr.20170516055435.2: *4* LeoMLTree.h_collapse_tree (done)
    def h_collapse_tree(self, ch):

        node = self.values[self.cursor_line]
        if native:
            p = node.content
            assert isinstance(p, leoNodes.Position)
            assert p
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
    #@+node:ekr.20170513091821.1: *4* LeoMLTree.h_cursor_line_down (revise)
    def h_cursor_line_down(self, ch):
        self.cursor_line += 1
        if self.cursor_line >= len(self.values):
            if self.scroll_exit: 
                self.cursor_line = len(self.values)-1
                self.h_exit_down(ch)
                return True
            else: 
                self.cursor_line -=1
                return True
        # else:
            # widget = self._my_widgets[self.cursor_line-self.start_display_at]
            # task = getattr(widget, 'task', None)
            # if task == self.continuation_line:
                # if self.slow_scroll:
                    # self.start_display_at += 1
                # else:
                    # self.start_display_at = self.cursor_line
    #@+node:ekr.20170513091928.1: *4* LeoMLTree.h_cursor_line_up (revise)
    def h_cursor_line_up(self, ch):
        self.cursor_line -= 1
        if self.cursor_line < 0: 
            if self.scroll_exit:
                self.cursor_line = 0
                self.h_exit_up(ch)
            else: 
                self.cursor_line = 0

    #@+node:ekr.20170506044733.12: *4* LeoMLTree.h_delete
    def h_delete(self, ch):

        self.delete_line()
    #@+node:ekr.20170506044733.10: *4* LeoMLTree.h_edit_headline
    def h_edit_headline(self, ch):
        
        self.edit_headline()
    #@+node:ekr.20170516055435.5: *4* LeoMLTree.h_expand_all (done)
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
    #@+node:ekr.20170516055435.3: *4* LeoMLTree.h_expand_tree (done)
    def h_expand_tree(self, ch):
       
        node = self.values[self.cursor_line]
        if native:
            p = node.content
            assert isinstance(p, leoNodes.Position)
            assert p
            p.v.expand()
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
    #@+node:ekr.20170506044733.11: *4* LeoMLTree.h_insert
    def h_insert(self, ch):

        return self.insert_line()
    #@+node:ekr.20170506035413.1: *4* LeoMLTree.h_move_left (done)
    def h_move_left(self, ch):
        
        node = self.values[self.cursor_line]
        if not node:
            g.trace('no node')
            return
        if native:
            p = node.content
            assert p and isinstance(p, leoNodes.Position), repr(p)
            if p.hasChildren() and p.isExpanded():
                self.h_collapse_tree(ch)
            else:
                self.h_cursor_line_up(ch)
            self.values.clear_cache()
        else:
            if self._has_children(node) and node.expanded:
                self.h_collapse_tree(ch)
            else:
                self.h_cursor_line_up(ch)
    #@+node:ekr.20170506035419.1: *4* LeoMLTree.h_move_right (done)
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
                self.h_cursor_line_down(ch)
        else:
            if self._has_children(node):
                if node.expanded:
                    self.h_cursor_line_down(ch)
                else:
                    self.h_expand_tree(ch)
            else:
                self.h_cursor_line_down(ch)
    #@+node:ekr.20170507175304.1: *4* LeoMLTree.set_handlers
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
    #@+node:ekr.20170516100256.1: *4* LeoMLTree.set_up_handlers
    def set_up_handlers(self):
        super(LeoMLTree, self).set_up_handlers()
        assert not hasattr(self, 'hidden_root_node'), repr(self)
        self.leo_c = None # Set later.
        self.currentItem = None
            # Used by CursesTree class.
        self.hidden_root_node = None
        self.set_handlers()

    #@+node:ekr.20170516055435.6: *4* LeoMLTree.set_up_handlers (REF)
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
    #@+node:ekr.20170513032502.1: *3* LeoMLTree.update (From MultiLine) & helpers
    def update(self, clear=True):
        '''Redraw the tree.'''
        # pylint: disable=access-member-before-definition
        if self.values is None:
            self.values = []
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
    #@+node:ekr.20170513122253.1: *4* LeoMLTree._init_update
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
    #@+node:ekr.20170513123010.1: *4* LeoMLTree._must_redraw
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
    #@+node:ekr.20170513032717.1: *4* LeoMLTree._print_line & helper
    def _print_line(self, line, i):

        ###
        # if self.widgets_inherit_color and self.do_colors():
            # line.color = self.color
        
        self._set_line_values(line, i)
            # Sets line.value
        if line.value is not None:
            assert isinstance(line.value, LeoTreeData), repr(line.value)
        self._set_line_highlighting(line, i)
    #@+node:ekr.20170513075423.1: *5* LeoMLTree_set_line_values
    def _set_line_values(self, line, i):
        '''Set internal values of line using self.values[i] and self.values[i+1]'''
        trace = False
        trace_ok = True
        trace_empty = False
        values = self.values
        n = len(values)
        val = values[i] if 0 <= i < n else None
        if not val:
            line._tree_real_value   = None
            line._tree_depth        = False
            line._tree_sibling_next = False
            line._tree_has_children = False
            line._tree_expanded     = False
            line._tree_last_line    = True #
            line._tree_depth_next   = False
            line._tree_ignore_root  = None
            #
            line.value = None
            line._tree_real_value = None
            if trace and trace_empty: g.trace(i, n, '<empty>')
            return
        assert isinstance(val, LeoTreeData), repr(val)
        val1 = values[i+1] if i+1 < n else None
        val1_depth = val1.find_depth() if val1 else False
        # 
        line.value = val # self.display_value(val)
        line._tree_real_value = val
        line._tree_ignore_root = self._get_ignore_root(self._myFullValues)
        # 
        line._tree_depth = val.find_depth()
        line._tree_has_children = len(val._children) > 0
        line._tree_expanded = val.expanded
        # 
        line._tree_sibling_next = line._tree_depth == val1_depth
        line._tree_last_line = not bool(line._tree_sibling_next)
        line._tree_depth_next = val1_depth
        if trace and trace_ok:
            content = line.value.content
            s = content.h if native else content
            g.trace(i, n, s)
    #@+node:ekr.20170513122427.1: *4* LeoMLTree._redraw & helper
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
            # Line is a LeoTreeLine object.
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
    #@+node:ekr.20170513102428.1: *5* LeoMLTree._put_continuation_line
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
    #@+node:ekr.20170516101203.1: *3* LeoMLTree.values Property (original only)
    if native:
        _myFullValues = LeoTreeData()
        values = []
    else:
        # This property converts the (possibly cached) result of converting
        # the root node (_myFullValues) and its *visible* decendants to a list.
        # To invalidate the cache, set __cached_tree = None
        #@+others
        #@+node:ekr.20170517142822.1: *4* _getValues
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

        #@+node:ekr.20170518054457.1: *4* _setValues
        def _setValues(self, tree):
            self._myFullValues = tree or LeoTreeData()
        #@-others
        values = property(_getValues, _setValues)

    if 0:
        # This works, even without the LeoVAlues class,
        # except that it has active blank lines at the end of the page.
        # This may be because the children of the last line are not visible.
        # However, this does no caching, so it is less good.
        _myFullValues = LeoTreeData()
        values = []
    #@+node:ekr.20170516084845.1: *3* LeoMLTree.XXX_MultiLine.make_contained_widgets

    def XXX_make_contained_widgets(self):
        ### Override MultiLine.make_contained_widgets
        trace = False
        trace_widgets = True
        self._my_widgets = []
        height = self.height // self.__class__._contained_widget_height
        if trace: g.trace(self.__class__.__name__, height) #, g.callers(2))
            # Called from BoxTitle.make_contained_widget.
        for h in range(height):
            ### EKR: it's LeoMLTree._contained_widgets that we have to emulate.
            self._my_widgets.append(
                self._contained_widgets(
                    self.parent, 
                    rely=(h*self._contained_widget_height)+self.rely, 
                    relx = self.relx, 
                    max_width=self.width, 
                    max_height=self.__class__._contained_widget_height
            ))
        if trace and trace_widgets:
            g.printList(self._my_widgets)
            g.printList(['value: %r' % (z.value) for z in self._my_widgets])
    #@-others
#@+node:ekr.20170517072429.1: ** class LeoValues (npyscreen.TreeData)
class LeoValues(npyscreen.TreeData):
    '''
    A class to replace the MLTree.values property.
    This is formally an subclass of TreeData.
    '''
    
    def __init__(self, c, tree):
        
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
    #@+node:ekr.20170517090738.1: *3* values.__getitem__ and get_data
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
            p = p.moveToVisNext(c)
            if p:
                self.position_cache[n] = p.copy()
                self.data_cache[n] = data = LeoTreeData(p.copy())
                if trace: g.trace(' after', n, repr(data))
                return data
            else:
                if trace: g.trace(' fail1', n, repr(data))
                return None
        # Search the tree, caching the result.
        i, p = 0, c.rootPosition()
        while p:
            if i == n:
                self.position_cache[n] = p.copy()
                self.data_cache[n] = data = LeoTreeData(p.copy())
                if trace: g.trace(' found', n, repr(data))
                return data
            else:
                p.moveToVisNext(c)
        if trace: g.trace(' fail2', n, repr(data))
        return None
    #@+node:ekr.20170518060014.1: *3* values.__len__
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
        return n
    #@+node:ekr.20170519041459.1: *3* values.clear_cache
    def clear_cache(self):
        
        self.data_cache = {}
        self.position_cache = {}
    #@+node:ekr.20170517143906.1: *3* values.get_values (not used yet)
    # def get_values(self):
        # g.trace(g.callers())
        # return []
    #@-others
#@-others
#@@language python
#@@tabwidth -4
#@-leo
