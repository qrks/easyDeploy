# encoding=utf-8
import sys
import os

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from win32com.client import Dispatch



def SendEmail(SendTo,CC,BCC,Subject,Body,Attachment=None,Pass=None):
    if SendTo==None:
        return
    session=Dispatch("Lotus.NotesSession")
    if Pass:
        session.Initialize(Pass)
    Server=session.GetEnvironmentString( "MailServer",True)

    print 'Server=%s' % Server

    MaildbName=session.GetEnvironmentString( "MailFile",True)

    print 'MaildbName=%s' % MaildbName

    db=session.GetDatabase(Server,MaildbName)

    # docl = db.getDocumentById('钱晓恺.id')
    # docl = db.getDocumentByUrl('')
    # docl = db.getProfileDocument('C:/Program Files/IBM/Lotus/Notes/Data/钱晓恺.id')
    # for v in db.views:
        # print v.name
    view = db.GetView("$Inbox")
    print type(view)
    print view

    print '---------------'
    print view.entrycount
    docl = view.getFirstDocument()
    for i in docl.items:
        print i
    subject = docl.getItemValue('Form')
    for t in subject:
        print t,type(t)

    doc=db.CreateDocument()

    doc.ReplaceItemValue("Form","Memo")
    if SendTo:
        doc.ReplaceItemValue("SendTo",SendTo)
    if CC:
        doc.ReplaceItemValue("CopyTo",SendTo)
    if BCC:
        doc.ReplaceItemValue("BlindCopyTo",SendTo)
    if Subject:
        doc.ReplaceItemValue("Subject",Subject)
    stream=session.CreateStream()
    stream.WriteText(Body)
    bodyMime=doc.CreateMIMEEntity()
    bodyMime.SetContentFromText(stream,"text/html;charset=iso-8859-1",False)
    if Attachment:
        RichTextItem = doc.CreateRichTextItem("Attachment")
        for fn in Attachment:
            RichTextItem.EmbedObject(1454, "", fn ,"Attachment")
    '''
    bodyMime=doc.CreateMIMEEntity()
    bodyMime.SetContentFromText(stream,"text/html;charset=iso-8859-1",False)
    doc.ReplaceItemValue( "Logo", "StdNotesLtr3" )
    doc.ReplaceItemValue( "_ViewIcon", 23 )
    doc.ReplaceItemValue( "SenderTag", "Y" )
    '''
    # doc.Send(False)


def main():
    # SendEmail("qianxiaokai@sh.icbc.com.cn",None,None,"Title:test","body:test for send mail",
    #     ["D:/tmp2/home/gtcg/GTCGProcessor/application/UPS/customer.xml"],"pass.234")
    SendEmail("qianxiaokai@sh.icbc.com.cn",None,None,"Title:test","body:test for send mail",
        None,'pass.234')

    print 'done'



if __name__ == '__main__':
    main()
    


