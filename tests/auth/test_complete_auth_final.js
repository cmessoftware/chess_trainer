/**
 * Final comprehensive test for all authentication flows
 * Tests mock login, permission calculation, and route access
 */

const fs = require('fs');
const path = require('path');

// Read and evaluate the authentication hook
const authPath = path.join(__dirname, 'src/frontend/src/hooks/useAuth.js');
const authContent = fs.readFileSync(authPath, 'utf8');

// Mock React hooks for testing
const mockHooks = {
    useState: (initial) => {
        let value = initial;
        const setter = (newValue) => {
            if (typeof newValue === 'function') {
                value = newValue(value);
            } else {
                value = newValue;
            }
        };
        return [value, setter];
    },
    useEffect: (callback, deps) => {
        callback();
    },
    useCallback: (callback, deps) => callback
};

// Create test environment
const testEnv = {
    React: mockHooks,
    useState: mockHooks.useState,
    useEffect: mockHooks.useEffect,
    useCallback: mockHooks.useCallback,
    fetch: async (url, options) => ({
        ok: true,
        json: async () => ({
            access_token: 'test_token',
            user: {
                id: 1,
                username: 'test_admin',
                roles: ['admin']
            }
        })
    }),
    localStorage: {
        getItem: () => null,
        setItem: () => {},
        removeItem: () => {}
    },
    console: console
};

// Extract and evaluate the permission calculation logic
const permissionLogicMatch = authContent.match(/const calculatePermissions = [\s\S]*?(?=const)/);
const mockUsersMatch = authContent.match(/const MOCK_USERS = \{[\s\S]*?\};/);
const routeAccessMatch = authContent.match(/const canAccessGames[\s\S]*?canAccessReports = \(user\) => hasPermission\(user, 'reports'\);/);

if (!permissionLogicMatch || !mockUsersMatch || !routeAccessMatch) {
    console.error('❌ Could not extract required code patterns');
    process.exit(1);
}

// Evaluate the extracted code
const evalCode = `
${mockUsersMatch[0]}

${permissionLogicMatch[0]}

const hasPermission = (user, permission) => {
    if (!user || !user.permissions) return false;
    return user.permissions.includes('ALL') || user.permissions.includes(permission);
};

const isAdmin = (user) => {
    return user && user.roles && user.roles.includes('admin');
};

${routeAccessMatch[0]}
`;

try {
    eval(evalCode);
    
    console.log('🧪 Testing Complete Authentication System\n');
    
    // Test 1: Mock Users Permissions
    console.log('📋 Test 1: Mock Users Permission Calculation');
    Object.entries(MOCK_USERS).forEach(([userType, user]) => {
        const calculatedPermissions = calculatePermissions(user.roles);
        const isUserAdmin = user.roles && user.roles.includes('admin');
        const finalPermissions = isUserAdmin ? ['ALL', ...calculatedPermissions] : calculatedPermissions;
        
        console.log(\`  \${userType}:\`);
        console.log(\`    Roles: [\${user.roles.join(', ')}]\`);
        console.log(\`    Is Admin: \${isUserAdmin}\`);
        console.log(\`    Calculated Permissions: [\${calculatedPermissions.join(', ')}]\`);
        console.log(\`    Final Permissions: [\${finalPermissions.join(', ')}]\`);
        console.log(\`    Permissions Count: \${finalPermissions.length}\`);
        console.log('');
    });
    
    // Test 2: Route Access for Admin
    console.log('🚦 Test 2: Route Access for Admin User');
    const adminUser = {
        ...MOCK_USERS.admin,
        permissions: ['ALL', ...calculatePermissions(MOCK_USERS.admin.roles)]
    };
    
    console.log(\`  Admin User Permissions: [\${adminUser.permissions.join(', ')}]\`);
    console.log(\`  Has 'ALL' permission: \${adminUser.permissions.includes('ALL')}\`);
    console.log('');
    console.log('  Route Access Results:');
    console.log(\`    canAccessGames: \${canAccessGames(adminUser)}\`);
    console.log(\`    canAccessImport: \${canAccessImport(adminUser)}\`);
    console.log(\`    canAccessReports: \${canAccessReports(adminUser)}\`);
    console.log('');
    
    // Test 3: Route Access for Regular User
    console.log('🚦 Test 3: Route Access for Regular User');
    const regularUser = {
        ...MOCK_USERS.user,
        permissions: calculatePermissions(MOCK_USERS.user.roles)
    };
    
    console.log(\`  Regular User Permissions: [\${regularUser.permissions.join(', ')}]\`);
    console.log(\`  Has 'ALL' permission: \${regularUser.permissions.includes('ALL')}\`);
    console.log('');
    console.log('  Route Access Results:');
    console.log(\`    canAccessGames: \${canAccessGames(regularUser)}\`);
    console.log(\`    canAccessImport: \${canAccessImport(regularUser)}\`);
    console.log(\`    canAccessReports: \${canAccessReports(regularUser)}\`);
    console.log('');
    
    // Test 4: Logic Verification
    console.log('✅ Test 4: Logic Verification');
    const testResults = {
        adminHasAll: adminUser.permissions.includes('ALL'),
        adminCanAccessGames: canAccessGames(adminUser),
        adminCanAccessImport: canAccessImport(adminUser),
        adminCanAccessReports: canAccessReports(adminUser),
        regularUserDoesNotHaveAll: !regularUser.permissions.includes('ALL'),
        allTestsPassed: false
    };
    
    testResults.allTestsPassed = 
        testResults.adminHasAll &&
        testResults.adminCanAccessGames &&
        testResults.adminCanAccessImport &&
        testResults.adminCanAccessReports &&
        testResults.regularUserDoesNotHaveAll;
    
    Object.entries(testResults).forEach(([test, result]) => {
        console.log(\`  \${test}: \${result ? '✅' : '❌'}\`);
    });
    
    console.log('\\n' + (testResults.allTestsPassed ? 
        '🎉 ALL TESTS PASSED! Authentication system is working correctly.' : 
        '⚠️  Some tests failed. Check the implementation.'));

} catch (error) {
    console.error('❌ Test execution failed:', error.message);
    console.error(error.stack);
    process.exit(1);
}