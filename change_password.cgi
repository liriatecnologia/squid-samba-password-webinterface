#!/usr/bin/env python3

'''
Web interface allowing users to change passwords for a Squid and
Samba servers at once. For information on how to install, see the
README file.

Author: Renato Candido <renato@liria.com.br>
Copyright 2012 Liria Tecnologia <http://www.liria.com.br>

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

Changelog:

2019-07-20
Migration to Python 3

2013-10-22
Improved templates by using Template Strings;
Implemented the possibility of using either Squid or Samba or both.

2012-10-22
Workaround to permit to change the script file name;
Improvements on error handling.

2012-10-15
Initial commit.
'''

import cgi
import os
from passlib.apache import HtpasswdFile
from passlib.hash import nthash
from textwrap import dedent
from string import Template

filename = os.path.basename(__file__)

################################################################################
# Config Area
################################################################################

# Password files
# Leave empty ("") if you do not wish to use
smbpasswd_path = "/etc/samba/smbpasswd"
# Leave empty ("") if you do not wish to use
squid_passwd_path = "/etc/squid/squid_passwd"

# Script directory on http server (if located at http://server-address/cgi-bin,
# this setting should be "/cgi-bin". Another example is "/scripts/cgi-bin" when
# the script is located at http://server-address/scripts/cgi-bin)
script_dir = "/cgi-bin"

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
base_template = Template(dedent(
    '''\
    Content-type: text/html
    
    <html>
      <head>
        <meta charset="UTF-8"> 
        <title>Mudança de senha dos servidores de dados e internet</title>
        $css
      </head>    
      <body>
        <div class="databox">
          <div class="boxtitle">
            Mudança de senha dos servidores de dados e internet
          </div>
          <div class="boxbody">
            $content
          </div>
        </div>
        <div class="liria">
          <a href="http://www.liria.com.br" target="_blank">Liria Tecnologia</a>
        </div>
      </body>
    </html>
    '''
))

# Form (fields used to change the passwords)
form = Template(dedent(
    '''\
    <form  method="post" id="change_password" action="$action">
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
))

# Response (where the success or error messages are presented)
response = Template(dedent(
    '''\
    <div class="msgbox">
      $message
    </div>
    <div class="back">
      <a href="$back">Voltar</a>
    </div>
    '''
))

# Messages

# Success messages
msg_success_squid = "Senha do servidor de internet alterada com sucesso."
msg_success_samba = "Senha do servidor de dados alterada com sucesso."
msg_success_2 = "Senha do servidor de dados e internet alterada com sucesso."
msg_success_0 = "Nenhuma senha alterada. Por favor configure para alterar as senhas do servidor de dados ou internet."

# Password confirmation does not match the new password
msg_error_new_password_2 = "Confirmação da nova senha não coincide com a senha digitada."

# Password too short (min. 4 characters)
msg_error_password_length = "A nova senha deve ter pelo menos 4 caracteres."

# Invalid current password
msg_error_current_password_squid = "Senha atual do servidor de internet incorreta."
msg_error_current_password_samba = "Senha atual do servidor de dados incorreta."

# User does not exist on Squid or Samba files
msg_error_invalid_user_squid = "Usuário não cadastrado no servidor de internet."
msg_error_invalid_user_samba = "Usuário não cadastrado no servidor de dados."

# Error when one of the fields is left blank
msg_error_invalid_data = "Dados inválidos. Por favor, preencha todos os campos."

# Error on changing the password of Squid or Samba (due to write
# permission on one of the files)
msg_error_setpassword_squid = "Erro ao alterar a senha do servidor de internet. Entre em contato com o administrador do sistema."
msg_error_setpassword_samba = "Erro ao alterar a senha do servidor de dados. Entre em contato com o administrador do sistema."

# Error on opening the Squid or Samba password files
msg_error_openfile_squid = "Arquivo de senhas do servidor de internet não encontrado. Entre em contato com o administrador do sistema."
msg_error_openfile_samba = "Arquivo de senhas do servidor de dados não encontrado. Entre em contato com o administrador do sistema."

################################################################################
# End of Config Area
################################################################################
msgs = (msg_success_squid,
        msg_success_samba,
        msg_success_2,
        msg_success_0,
        msg_error_new_password_2,
        msg_error_password_length,
        msg_error_current_password_squid,
        msg_error_current_password_samba,
        msg_error_invalid_user_squid,
        msg_error_invalid_user_samba,
        msg_error_invalid_data,
        msg_error_setpassword_squid,
        msg_error_setpassword_samba,
        msg_error_openfile_squid,
        msg_error_openfile_samba,
        )

# Append script location and name to the templates
script_location = script_dir + "/" + filename
form = form.safe_substitute(action=script_location)
response = response.safe_substitute(back=script_location)

form = base_template.safe_substitute(css=css, content=form)
response = Template(base_template.safe_substitute(css=css, content=response))


def process_cgi(smbpasswd_path, squid_passwd_path, form, response, msgs):
    """
    Main function
    Processes the CGI information
    """
    form_data = cgi.FieldStorage()

    use_squid = not(squid_passwd_path == '')
    use_samba = not(smbpasswd_path == '')
    change_ok_samba = False
    change_ok_squid = False

    msg_success_squid = msgs[0]
    msg_success_samba = msgs[1]
    msg_success_2 = msgs[2]
    msg_success_0 = msgs[3]
    msg_error_new_password_2 = msgs[4]
    msg_error_password_length = msgs[5]
    msg_error_current_password_squid = msgs[6]
    msg_error_current_password_samba = msgs[7]
    msg_error_invalid_user_squid = msgs[8]
    msg_error_invalid_user_samba = msgs[9]
    msg_error_invalid_data = msgs[10]
    msg_error_setpassword_squid = msgs[11]
    msg_error_setpassword_samba = msgs[12]
    msg_error_openfile_squid = msgs[13]
    msg_error_openfile_samba = msgs[14]

    if "submit" in form_data:
        if ("user" in form_data and "current_password" in form_data and
                "new_password" in form_data and "new_password_2" in form_data):
            user = form_data.getvalue("user")
            current_password = form_data.getvalue("current_password")
            new_password = form_data.getvalue("new_password")
            new_password_2 = form_data.getvalue("new_password_2")
            if len(new_password) >= 4:
                if new_password == new_password_2:
                    if use_squid:
                        try:
                            squid_passwd = HtpasswdFile(squid_passwd_path)
                        except IOError:
                            msg = msg_error_openfile_squid
                            print(response.safe_substitute(message=msg))
                            return
                    if use_samba:
                        try:
                            smbpasswd = SmbpasswdFile(smbpasswd_path)
                        except IOError:
                            msg = msg_error_openfile_samba
                            print(response.safe_substitute(message=msg))
                            return

                    if use_samba:
                        smb_password_resp = smbpasswd.check_password(
                            user, current_password)
                        if smb_password_resp is not None:
                            if smb_password_resp == True:
                                change_ok_samba = True
                                try:
                                    smbpasswd.set_password(user, new_password)
                                    smbpasswd.save()
                                except:
                                    msg = msg_error_setpassword_samba
                                    change_ok_samba = False
                                    print(response.safe_substitute(message=msg))
                                    return
                            else:
                                msg = msg_error_current_password_samba
                                print(response.safe_substitute(message=msg))
                                return
                        else:
                            msg = msg_error_invalid_user_samba
                            print(response.safe_substitute(message=msg))
                            return

                    if use_squid:
                        if (use_samba and change_ok_samba) or not(use_samba):
                            squid_password_resp = squid_passwd.check_password(
                                user, current_password)
                            if squid_password_resp is not None:
                                if squid_password_resp == True:
                                    change_ok_squid = True
                                    try:
                                        squid_passwd.set_password(
                                            user, new_password)
                                        squid_passwd.save()
                                    except:
                                        msg = msg_error_setpassword_squid
                                        change_ok_squid = False
                                else:
                                    msg = msg_error_current_password_squid
                            else:
                                msg = msg_error_invalid_user_squid

                            if change_ok_samba and not(change_ok_squid):
                                smbpasswd.set_password(user, current_password)
                                smbpasswd.save()
                                print(response.safe_substitute(message=msg))
                                return

                    if use_samba:
                        if use_squid:
                            if change_ok_samba and change_ok_squid:
                                msg = msg_success_2
                        else:
                            if change_ok_samba:
                                msg = msg_success_samba
                    else:
                        if use_squid:
                            if change_ok_squid:
                                msg = msg_success_squid
                        else:
                            msg = msg_success_0
                else:
                    msg = msg_error_new_password_2
            else:
                msg = msg_error_password_length
        else:
            msg = msg_error_invalid_data

        print(response.safe_substitute(message=msg))
    else:
        print(form)


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
                               key=lambda dic_value: dic_value[-1]):

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
    for i, smbpasswd_item in enumerate(smbpasswd_list):
        smbpasswd_list[i] = smbpasswd_item.split(':')
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
