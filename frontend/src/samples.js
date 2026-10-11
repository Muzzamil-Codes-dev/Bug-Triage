export const SAMPLE_REPORTS = [
  {
    label: "Checkout outage",
    text: `Title: Checkout fails with HTTP 500 after v2.14 deploy

Since this morning's deploy of v2.14 to production, customers clicking 'Place order' get an HTTP 500. About 30% of checkout attempts are failing according to the dashboard.

Service: payments-service
Environment: production

Logs:
2026-10-11T09:14:02Z ERROR payments-service OrderController - NullPointerException at PaymentGatewayClient.charge(PaymentGatewayClient.java:88)
2026-10-11T09:14:05Z ERROR payments-service OrderController - NullPointerException at PaymentGatewayClient.charge(PaymentGatewayClient.java:88)

Steps to reproduce:
1. Add any item to cart
2. Go to checkout and pay with a saved card
3. Click Place order

Recent changes: v2.14 refactored PaymentGatewayClient to read the gateway timeout from a new config key payments.gateway.timeout.`,
  },
  {
    label: "Login after password reset",
    text: `Users who reset their password cannot log in afterwards. They see 'Something went wrong' and the request returns HTTP 500. Reported by 12 customers since yesterday.

Service: auth-api
Environment: production

Stack trace:
Traceback (most recent call last):
  File "auth/views.py", line 142, in login
    session.user_id = user.id
AttributeError: 'NoneType' object has no attribute 'id'

Steps:
1. Click 'Forgot password' and reset it via the email link
2. Log in with the new password

Recent changes: Password reset tokens were moved from Redis to Postgres last week.`,
  },
  {
    label: "Minor UI glitch",
    text: `On the account settings page, the 'Save changes' button overlaps the footer on screens narrower than 360px, so part of the button can't be clicked. Changes still save if you scroll a bit. Seen on Chrome for Android, staging environment. Only affects small phones.`,
  },
];
