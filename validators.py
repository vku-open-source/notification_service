from marshmallow import Schema, fields, validate

class NotificationChannelsSchema(Schema):
    email = fields.Bool(required=True)
    sms = fields.Bool(required=True)

class RecipientSchema(Schema):
    email = fields.Email(required=True)
    phone = fields.Str(required=True)
    notification_channels = fields.Nested(NotificationChannelsSchema, required=True)

class NotificationSchema(Schema):
    type = fields.Str(required=True, validate=validate.OneOf(['emergency_alert']))
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    content = fields.Str(required=True, validate=validate.Length(min=1, max=1000))
    recipients = fields.List(fields.Nested(RecipientSchema), required=True)

