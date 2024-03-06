import os
import uuid
from resemble.aio.contexts import ReaderContext, WriterContext
from resemble.aio.tasks import TaskEffect
from resemble.examples.boutique.api import demo_pb2
from resemble.examples.boutique.api.demo_rsm import Emailer
# Import the whole `mailgun` module, and not only the `mailgun.send_email`
# method, so that tests can still mock `mailgun.send_email` for us.
from resemble.examples.boutique.backend.helpers import mailgun
from typing import Optional


class MailgunServicer(Emailer.Interface):

    async def SendEmailTask(
        self,
        context: ReaderContext,
        state: demo_pb2.EmailerState,
        request: demo_pb2.SendEmailTaskRequest,
    ) -> demo_pb2.SendEmailTaskResponse:
        mailer = mailgun.Mailgun(os.environ['MAILGUN_API_KEY'].strip())

        text: Optional[str] = (
            request.request.text if request.request.HasField('text') else None
        )

        html: Optional[str] = (
            request.request.html if request.request.HasField('html') else None
        )

        if (
            (text is not None and html is not None) or
            (text is None and html is None)
        ):
            raise ValueError(
                "Exactly one of 'text' or 'html' should be specified"
            )

        body = text or html
        body_type = 'text' if text is not None else 'html'

        assert body is not None

        await mailer.send_email_idempotently(
            sender=request.request.sender,
            recipient=request.request.recipient,
            subject=request.request.subject,
            domain='reboot.dev',
            idempotency_key=request.id,
            body=body,
            body_type=body_type,
        )

        return demo_pb2.SendEmailTaskResponse()

    async def PrepareSendEmail(
        self,
        context: WriterContext,
        state: demo_pb2.EmailerState,
        request: demo_pb2.PrepareSendEmailRequest,
    ) -> Emailer.PrepareSendEmailEffects:
        task: TaskEffect = self.schedule().SendEmailTask(
            context,
            request=request,
            id=str(uuid.uuid4()),
        )
        return Emailer.PrepareSendEmailEffects(
            state=state,
            tasks=[task],
            response=demo_pb2.PrepareSendEmailResponse(
                # TODO(rjh, riley): for reasons explained in the proto, we can't
                # just return a Resemble `TaskId` here; we need to construct a
                # different `TaskId` that lives in the same `.proto` file as the
                # rest of our service.
                email_task=demo_pb2.TaskId(
                    service=task.task_id.service,
                    actor_id=task.task_id.actor_id,
                    task_uuid=task.task_id.task_uuid,
                ),
            ),
        )
