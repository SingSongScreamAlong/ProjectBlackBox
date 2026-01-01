# Squarespace Billing Integration

## Overview
Ok, Box Box uses Squarespace Commerce for billing. Squarespace sends webhooks to our server when orders are created/updated, and we provision entitlements accordingly.

## SKU Mapping

### Base Products
| SKU | Product | Scope | Price |
|-----|---------|-------|-------|
| `BB-MONTHLY` | blackbox | user | $16/mo |
| `BB-ANNUAL` | blackbox | user | $153.60/yr |
| `CB-MONTHLY` | controlbox | org | $18/mo |
| `CB-ANNUAL` | controlbox | org | $172.80/yr |
| `RBX-PLUS-MONTHLY` | racebox_plus | org | $15/mo |
| `RBX-PLUS-ANNUAL` | racebox_plus | org | $144/yr |
| `BUNDLE-MONTHLY` | bundle | user+org | $40/mo |
| `BUNDLE-ANNUAL` | bundle | user+org | $384/yr |

### Series Add-ons
| SKU | For Product | Price |
|-----|-------------|-------|
| `CB-SERIES-ADDON` | controlbox | $2/mo per series |
| `RBX-SERIES-ADDON` | racebox_plus | $2/mo per series |

Series add-ons are quantity-aware. Purchasing qty 3 adds 3 series to the org's entitlement.

## Environment Variables
```
SQUARESPACE_WEBHOOK_SECRET=your_webhook_secret
SQUARESPACE_API_KEY=your_api_key
```

## Webhook Events
- `order.create` → Create entitlement
- `order.update` (FULFILLED) → Renew entitlement
- `order.update` (CANCELED/REFUNDED) → Revoke entitlement

## Testing Locally

1. **Set env vars:**
   ```bash
   export SQUARESPACE_WEBHOOK_SECRET=test_secret
   export SQUARESPACE_API_KEY=test_key
   ```

2. **Start server:**
   ```bash
   npm run dev --workspace=packages/server
   ```

3. **Simulate webhook:**
   ```bash
   curl -X POST http://localhost:3001/api/billing/squarespace/webhook \
     -H "Content-Type: application/json" \
     -d '{"topic":"order.create","data":{"orderId":"test-123"}}'
   ```

4. **Verify entitlement:**
   ```sql
   SELECT * FROM entitlements WHERE external_order_id = 'test-123';
   ```
