# Midway Authentication Integration Guide

This document explains how to integrate Midway authentication with the ProCert Learning Platform.

## Current Setup

The platform currently supports:
- **Cognito User Pool**: Direct email/password authentication
- **Self-registration**: Users can create accounts via API
- **JWT tokens**: For API access after authentication

## Midway Integration Options

### Option 1: SAML Federation (Recommended)

Configure Cognito User Pool to accept SAML assertions from Midway:

1. **Get Midway SAML Metadata**:
   - Contact your AWS IT team for Midway SAML metadata URL
   - Typical format: `https://midway.amazon.com/saml/metadata`

2. **Update CDK Stack**:
   ```python
   # Uncomment and configure in procert_infrastructure_stack.py
   midway_saml_provider = cognito.CfnUserPoolIdentityProvider(self, "MidwaySAMLProvider",
       user_pool_id=self.user_pool.user_pool_id,
       provider_name="Midway",
       provider_type="SAML",
       attribute_mapping={
           "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
           "given_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname", 
           "family_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
       },
       provider_details={
           "MetadataURL": "ACTUAL_MIDWAY_METADATA_URL",
           "SSORedirectBindingURI": "ACTUAL_MIDWAY_SSO_URL",
           "SLORedirectBindingURI": "ACTUAL_MIDWAY_SLO_URL"
       }
   )
   ```

3. **Update User Pool Client**:
   ```python
   self.user_pool_client.add_property_override("SupportedIdentityProviders", ["COGNITO", "Midway"])
   ```

### Option 2: Direct OIDC Integration

If Midway supports OIDC:

```python
midway_oidc_provider = cognito.CfnUserPoolIdentityProvider(self, "MidwayOIDCProvider",
    user_pool_id=self.user_pool.user_pool_id,
    provider_name="Midway",
    provider_type="OIDC",
    attribute_mapping={
        "email": "email",
        "given_name": "given_name",
        "family_name": "family_name"
    },
    provider_details={
        "client_id": "YOUR_MIDWAY_CLIENT_ID",
        "client_secret": "YOUR_MIDWAY_CLIENT_SECRET",
        "authorize_scopes": "openid email profile",
        "oidc_issuer": "https://midway.amazon.com"
    }
)
```

## User Experience

### With Midway Integration

1. **User visits login page**
2. **Chooses authentication method**:
   - "Sign in with Midway" (federated)
   - "Sign in with email" (direct Cognito)
3. **Midway users**: Redirected to Midway, then back with JWT tokens
4. **Direct users**: Use email/password as before

### API Access Remains the Same

```bash
# All users get the same JWT tokens regardless of auth method
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Implementation Steps

### Phase 1: Prepare Infrastructure
1. Update CDK stack with commented Midway configuration
2. Deploy current simplified version (no subscription tiers)
3. Test current functionality

### Phase 2: Get Midway Details
1. Contact AWS IT for Midway integration requirements
2. Get SAML metadata URL and configuration details
3. Register ProCert as a Midway application

### Phase 3: Enable Midway
1. Uncomment and configure Midway provider in CDK
2. Update frontend to show both login options
3. Test federated authentication flow

## Benefits

- **Seamless for AWS employees**: Single sign-on with corporate credentials
- **Demo-friendly**: Still supports direct email/password for external demos
- **Security**: Leverages corporate identity management
- **Compliance**: Meets internal AWS authentication requirements

## Next Steps

1. **Immediate**: Deploy simplified system (remove subscription tiers)
2. **Short-term**: Contact AWS IT about Midway integration requirements
3. **Medium-term**: Implement federated authentication
4. **Long-term**: Consider making Midway the primary authentication method

## Testing Current System

Create test users via:

```bash
# Via API
POST /auth/register
{
  "email": "test@amazon.com",
  "password": "TestPass123",
  "given_name": "Test",
  "family_name": "User"
}

# Via AWS CLI
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username test@amazon.com \
  --user-attributes Name=email,Value=test@amazon.com \
  --temporary-password TempPass123!
```