#!/usr/bin/env python
# -*- encoding: utf-8 -*-

'''
Web interface allowing users to change passwords for a Squid and
Samba servers at once. For information on how to install, see the
README file.

Copyright 2012 Liria Tecnologia

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import cgi
from passlib.apache import HtpasswdFile
from passlib.hash import nthash
from textwrap import dedent

################################################################################
# Config Area
################################################################################

# Password files
smbpasswd_path = "/etc/samba/smbpasswd"
squid_passwd_path = "/etc/squid/squid_passwd"

# CSS Styles
css = dedent(
    '''
    <style type="text/css" media="screen">
      body {
      background-color: #CCCCCC;
      font-family: "Verdana", sans-serif;
      }
    
      input.text {
      width: 280px;
      }
    
      .databox {
      -moz-border-radius: 15px;
      border-radius: 15px;
      background-color: white;
      margin: 10px;
      border: 10px;
      width: 550px;
      height: 220px;
      position: absolute;
      top: 50%;
      left: 50%;
      margin-top: -110px;
      margin-left: -300px;
      }
    
      .boxtitle {
      text-align: center;
      padding: 7px;
      background-color: black;
      -moz-border-radius: 15px;
      border-radius: 15px;
      border-bottom-left-radius: 0px 0px;
      border-bottom-right-radius: 0px 0px;
      color: white;
      }
    
      .boxbody {
      padding: 10px;
      }
    
      .msgbox {
      margin-top: 20px;
      padding: 10px;
      text-align: center;
      background-color: #FFFF77;
      color: red;
      }
    
      .back {
      margin-top: 20px;
      text-align: center;
      }
    
      td.label {
      text-align: right;
      }
    
      td.table_footer {
      text-align: center;
      }

      td.textinfo {
      font-size: 13px;
      }

      .liria {
      font-family: "Helvetica", sans-serif;
      font-size: 13px;
      position: absolute;
      top: 95%;
      text-align: center;
      width: 95%;
      }      
    </style>
    '''
    )

# Base template
template = dedent(
    '''\
    Content-type: text/html
    
    <html>
      <head>
        <meta charset="UTF-8"> 
        <title>Mudança de senha dos servidores de dados e internet</title>
        %s
      </head>    
      <body>
        <div class="databox">
          <div class="boxtitle">
            Mudança de senha dos servidores de dados e internet
          </div>
          <div class="boxbody">
            %s
          </div>
        </div>
        <div class="liria">
          <a href="http://www.liria.com.br" target="_blank">Liria Tecnologia</a>
        </div>
      </body>
    </html>
    '''
    )

# Form (fields used to change the passwords)
form = dedent(
    '''\
    <form  method="post" id="change_password" action="/cgi-bin/change_password.py">
      <table width="100%" cellspacing="0px" cellpadding="2px" border="0">
        <tr>
          <td class="label">Usuário:</td><td><input class="text" type="text" name="user" value="" /></td>
        </tr>
        <tr>
          <td class="label">Senha Atual:</td><td><input class="text" type="password" name="current_password" value="" /></td>
        </tr>
        <tr>
          <td class="label">Nova senha:</td><td><input class="text" type="password" name="new_password" value="" /></td>
        </tr>
        <tr>
        <td></td><td class="textinfo">* Mínimo de 4 caracteres</td>
        </tr>
        <tr>
          <td class="label">Confirmação da nova senha:</td><td><input class="text" type="password" name="new_password_2" value="" /></td>
        </tr> 
        <tr>
          <td class="table_footer" colspan="2"><input type="submit" name="submit" value="Mudar a senha" /></td>
        </tr>
      </table>
    </form>
    '''
    )

# Response (where the success or error messages are presented)
response = dedent(
    '''\
    <div class="msgbox">
      %s
    </div>
    <div class="back">
      <a href="/cgi-bin/change_password.py">Voltar</a>
    </div>
    '''
    )
                                          
# Messages

# Success message
msg_success = "Senha alterada com sucesso"

# Password confirmation does not match the new password
msg_error_new_password_2 = "Confirmação da nova senha não coincide com a senha digitada"

# Password too short (min. 4 characters)
msg_error_password_length = "A nova senha deve ter pelo menos 4 caracteres"

# Invalid current password
msg_error_current_password = "Senha atual incorreta"

# User does not exist
msg_error_invalid_user = "Usuário não cadastrado"

# Error when one of the fields is left blank
msg_error_invalid_data = "Dados inválidos"

# Error on changing the password either on Squid or Samba (verification after
# the password change does not match the new password)
msg_error_setpassword = "Erro ao alterar a senha. Entre em contato com o administrador do sistema"

# Error on opening the Squid or Samba password files
msg_error_openfile = "Arquivo de senhas não encontrado. Entre em contato com o administrador do sistema."

################################################################################
# End of Config Area
################################################################################

msgs = (msg_success,
        msg_error_new_password_2,
        msg_error_password_length,
        msg_error_current_password,
        msg_error_invalid_user,
        msg_error_invalid_data,
        msg_error_setpassword,
        msg_error_openfile,
        )

form = template % (css, form)
response = template % ('%s', response) % (css.replace('%', '%%'), '%s')

def process_cgi(smbpasswd_path, squid_passwd_path, form, response, msgs):
    """
    Main function
    Processes the CGI information
    """
    form_data = cgi.FieldStorage()

    msg_success = msgs[0]
    msg_error_new_password_2 = msgs[1]
    msg_error_password_length = msgs[2]
    msg_error_current_password = msgs[3]
    msg_error_invalid_user = msgs[4]
    msg_error_invalid_data = msgs[5]
    msg_error_setpassword = msgs[6]
    msg_error_openfile = msgs[7]
    
    if "submit" in form_data:
        if ("user" in form_data and "current_password" in form_data and
            "new_password" in form_data and "new_password_2" in form_data):
            user = form_data.getvalue("user")
            current_password = form_data.getvalue("current_password")
            new_password = form_data.getvalue("new_password")
            new_password_2 = form_data.getvalue("new_password_2")
            
            try:
                smbpasswd = SmbpasswdFile(smbpasswd_path)
            except IOError:
                msg = msg_error_openfile
                print response % msg
                return
            try:
                squid_passwd = HtpasswdFile(squid_passwd_path)
            except IOError:
                msg = msg_error_openfile
                print response % msg
                return

            smb_password_resp = smbpasswd.check_password(user, current_password)
            if smb_password_resp is not None:
                if smb_password_resp == True:
                    if len(new_password) >= 4:
                        if new_password == new_password_2:
                            smbpasswd.set_password(user, new_password)
                            smbpasswd.save()
                            squid_passwd.set_password(user, new_password)
                            squid_passwd.save()
                            if smbpasswd.check_password(user, new_password):
                                if squid_passwd.check_password(user,
                                                               new_password):
                                    msg = msg_success
                                else:
                                    msg = msg_error_setpassword
                            else:
                                msg = msg_error_setpassword
                        else:
                            msg = msg_error_new_password_2
                    else:
                        msg = msg_error_password_length
                else:
                    msg = msg_error_current_password
            else:
                msg = msg_error_invalid_user
        else:
            msg = msg_error_invalid_data
            
        print response % msg
    else:
        print form

class SmbpasswdFile(object):
    """
    Deals with passwords of a smbpasswd file, allowing check through the
    check_password method and set through the set_password method
    """
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.username = ''
        self.hash = ''
        self.user_exists = False
        smbpasswd_file = open(filepath)
        smbpasswd_file.close()

    def check_password(self, username, password):
        """
        Checks smbpasswd file for a user's password
        """
        smbpasswd_dic = make_dic_from_smbpasswd(self.filepath)
        try:
            stored_hash = smbpasswd_dic[username][3].upper()
        except KeyError:
            return
        computed_hash = nthash.encrypt(password).upper()
        if stored_hash == computed_hash:
            return True
        else:
            return False

    def set_password(self, username, password):
        """
        Prepares the SmbPasswd instance with the username that will be
        updated and the hash that needs to be stored in smbpasswd file
        """
        self.username = username
        self.hash = nthash.encrypt(password).upper()
        self.user_exists = True
        smbpasswd_dic = make_dic_from_smbpasswd(self.filepath)
        try:
            smbpasswd_dic[username]
        except KeyError:
            self.user_exists = False

        return self.user_exists

    def save(self):
        """
        Saves the new user's hash in smbpasswd file
        """
        if self.user_exists:
            smbpasswd_dic = make_dic_from_smbpasswd(self.filepath)
            smbpasswd_dic[self.username][3] = self.hash
            smbpasswd_new_contents = ''

            # For each list ([param1, ..., param6, position]) contained
            # on the dictionary, sorting them by the original line number
            # of the read smbpasswd file (dictionaries do not care about
            # the position of the items)
            for item in sorted(smbpasswd_dic.values(),
                               key = lambda dic_value: dic_value[-1]):

                # Remove position (line number) information
                item = item[0:-1]

                for subitem in item:
                    smbpasswd_new_contents = (smbpasswd_new_contents
                                              + subitem + ':')
                smbpasswd_new_contents = smbpasswd_new_contents[0:-1]
                smbpasswd_new_contents = smbpasswd_new_contents + "\n"
            smbpasswd_new_contents = smbpasswd_new_contents[0:-1]

            smbpasswd_file = open(self.filepath, 'w')
            smbpasswd_file.write(smbpasswd_new_contents)
            smbpasswd_file.close()
        else:
            raise UserDoesNotExist

def make_dic_from_smbpasswd(filepath):
    """
    Returns a dictionary with elements
    'username':[param1, param2, param3, param4, param5, param6, position],
    where the params refer to the user's parameters stored on the smbpasswd
    file and position refers to the line number of the item on smbpasswd
    file.
    """
    smbpasswd_file = open(filepath)
    smbpasswd_contents = smbpasswd_file.read()
    smbpasswd_file.close()
    
    smbpasswd_list = smbpasswd_contents.split('\n')
    for i in range(len(smbpasswd_list)):
        smbpasswd_list[i] = smbpasswd_list[i].split(':')
        # Line number of the item on the last index of the list
        # smbpasswd_list[i] (starting at 0)
        smbpasswd_list[i].append(i)

    smbpasswd_dic = {}

    for item in smbpasswd_list:
        smbpasswd_dic[item[0]] = item

    return smbpasswd_dic

class UserDoesNotExist(Exception):
    """
    Exception raised when trying to save a password of a user that does not
    exist on smbpasswd file
    """

process_cgi(smbpasswd_path, squid_passwd_path, form, response, msgs)
