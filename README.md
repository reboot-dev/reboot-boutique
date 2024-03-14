To start the Resemble boutique backend you need to make sure you have
secrets in place; you need the `mailgun-api-key` secret in the
directory `backend/secrets`.

```shell
mkdir secrets
```

Replace `MY_MAILGUN_API_KEY` with your own mailgun API key, which you can get from [your Mailgun account](https://www.mailgun.com):
```shell
echo -n "MY_MAILGUN_API_KEY" >secrets/mailgun-api-key
```

If you are using Reboot Cloud, read [the documentation about `rsm secret`](https://docs.reboot.dev/docs/concepts/secrets) to learn how to set a secret.

Then you can do development:

```shell
rsm dev
```
