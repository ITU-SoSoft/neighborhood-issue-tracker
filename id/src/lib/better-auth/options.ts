import { BetterAuthOptions } from 'better-auth';
import { openAPI, jwt, organization } from 'better-auth/plugins';

/**
 * Custom options for Better Auth
 *
 * Docs: https://www.better-auth.com/docs/reference/options
 */
export const betterAuthOptions: BetterAuthOptions = {
  /**
   * The name of the application.
   */
  appName: 'sosoft-id',
  /**
   * Base path for Better Auth.
   * @default "/api/auth"
   */
  basePath: '/api/auth', // default is good

  /**
   * User model customization
   */
  user: {
    additionalFields: {
      isSuperAdmin: {
        type: 'boolean',
        required: false,
        defaultValue: false,
        input: false, // Users cannot set this themselves - must be set via database
      },
    },
  },

  /**
   * Plugins
   */
  plugins: [
    openAPI({
      path: '/reference', // Access at /api/auth/reference
      theme: 'purple', // Scalar theme: default, moon, purple, solarized, etc.
    }),
    jwt(), // JSON Web Token support
    organization({
      // Only users with isSuperAdmin=true can create organizations (support teams)
      allowUserToCreateOrganization: false,
      
      // Define organization roles (Better Auth uses 'member' and 'admin')
      // In your app: member=support, admin=manager
      roles: {
        member: {
          name: 'Support',
          description: 'Support team member who can handle issues',
          permissions: [
            'issue:read',
            'issue:write',
            'issue:comment',
          ],
        },
        admin: {
          name: 'Manager',
          description: 'Team manager who can manage their team',
          permissions: [
            'issue:read',
            'issue:write',
            'issue:comment',
            'issue:assign',
            'team:read',
            'team:invite',
            'team:remove_member',
          ],
        },
      },
    }),
  ],

  // .... More options
};
