import { BetterAuthOptions } from 'better-auth';
import { openAPI, jwt } from 'better-auth/plugins';

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
   * Plugins
   */
  plugins: [
    openAPI({
      path: '/reference', // Access at /api/auth/reference
      theme: 'purple', // Scalar theme: default, moon, purple, solarized, etc.
    }),
    jwt(), // JSON Web Token support
  ],

  // .... More options
};
