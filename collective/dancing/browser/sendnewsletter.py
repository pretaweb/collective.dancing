import datetime

from zope import interface
from zope import schema

from zope.app.pagetemplate import viewpagetemplatefile

from z3c.form import form
from z3c.form import subform
from z3c.form import field
from z3c.form import button
from z3c.form import validator
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.z3cform import z2
import collective.singing.scheduler

from collective.dancing import MessageFactory as _
from collective.dancing.composer import FullFormatWrapper
from collective.dancing.browser.interfaces import ISendAndPreviewForm

class SendAsNewsletterForm(form.Form):
    template = viewpagetemplatefile.ViewPageTemplateFile('form.pt')
    
    ignoreContext = True

    fields = field.Fields(ISendAndPreviewForm)

    @button.buttonAndHandler(_('Send'), name='send')
    def handle_send(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = form.EditForm.formErrorsMessage
            return
        channels = data['channels']
        include_collector_items = data['include_collector_items']

        queued = 0
        for channel in channels:
            queued += collective.singing.scheduler.assemble_messages(
                channel,
                self.request,
                (FullFormatWrapper(self.context),),                
                include_collector_items)
            if channel.scheduler is not None and include_collector_items:
                channel.scheduler.triggered_last = datetime.datetime.now()

        self.status = _(u"${num} messages queued.", mapping=dict(num=queued))

    @button.buttonAndHandler(_('Show preview'), name='show_preview')
    def handle_show_preview(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = form.EditForm.formErrorsMessage
            return

        channels = data['channels']
        if len(channels) != 1:
            self.status = _(u"Please select precisely one channel for preview.")
            return

        name = tuple(channels)[0].name
        include_collector_items = data['include_collector_items']
        
        self.request.response.redirect(
            self.context.absolute_url()+\
            '/preview-newsletter.html?name=%s&include_collector_items=%d' % \
            (name, int(bool(include_collector_items))))

    @button.buttonAndHandler(_('Send preview'), name='preview')
    def handle_preview(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = form.EditForm.formErrorsMessage
            return
        channels = data['channels']
        include_collector_items = data['include_collector_items']
        address = data['address']

        queued = 0
        for channel in channels:
            subs = channel.subscriptions.query(key=address)
            if len(subs) == 0:
                self.status = _(
                    u"${address} is not subscribed to ${channel}.",
                    mapping=dict(address=address, channel=channel.title))
                continue

            for sub in subs:
                collective.singing.scheduler.render_message(
                    channel,
                    self.request,
                    sub,
                    (FullFormatWrapper(self.context),),                
                    include_collector_items)
                queued += 1
        if queued:
            self.status = _(
                u"${num} messages queued.", mapping=dict(num=queued))

class SendAsNewsletterView(BrowserView):
    __call__ = ViewPageTemplateFile('controlpanel.pt')

    def label(self):
        return _(u'Send ${item} as newsletter',
                 mapping=dict(item=self.context.title))

    def contents(self):
        z2.switch_on(self,
                     request_layer=collective.singing.interfaces.IFormLayer)
        return SendAsNewsletterForm(self.context, self.request)()
