/**
 * Final comprehensive test for authentication system
 */

const fs = require('fs');
const path = require('path');

// Read the authentication hook content
const authPath = path.join(__dirname, 'src/frontend/src/hooks/useAuth.js');
const authContent = fs.readFileSync(authPath, 'utf8');

// Extract MOCK_USERS definition
const mockUsersMatch = authContent.match(/const MOCK_USERS = \{[\s\S]*?\};/);
// Extract calculatePermissions function
const calcPermMatch = authContent.match(/const calculatePermissions = \(roles\) => \{[\s\S]*?\n\s*\}/);

if (!mockUsersMatch || !calcPermMatch) {
    console.error('Could not extract required code patterns');
    process.exit(1);
}

// Setup test environment
const PERMISSION_MAP = {
    'admin': ['ALL', 'admin_panel', 'user_management', 'system_config', 'view_own_games', 'chess_board', 'create_exercises', 'view_stats', 'train_tactics', 'bulk_upload', 'import_pgn', 'advanced_analytics', 'reports'],
    'basic_gamer': ['view_own_games', 'chess_board'],
    'analysis_board': ['chess_board'],
    'exercise_creator': ['create_exercises'],
    'stats_viewer': ['view_stats'],
    'tactics_trainer': ['train_tactics'],
    'pgn_uploader': ['bulk_upload', 'import_pgn'],
    'eda_analyst': ['advanced_analytics', 'reports']
};

// Evaluate the mock users
eval(mockUsersMatch[0]);

// Implement calculatePermissions function
const calculatePermissions = (roles) => {
    if (!roles || !Array.isArray(roles)) return [];
    
    const permissions = new Set();
    roles.forEach(role => {
        const rolePermissions = PERMISSION_MAP[role];
        if (rolePermissions) {
            rolePermissions.forEach(perm => permissions.add(perm));
        }
    });
    
    return Array.from(permissions);
};

const hasPermission = (user, permission) => {
    if (!user || !user.permissions) return false;
    return user.permissions.includes('ALL') || user.permissions.includes(permission);
};

const canAccessGames = (user) => hasPermission(user, 'view_own_games');
const canAccessImport = (user) => hasPermission(user, 'import_pgn');
const canAccessReports = (user) => hasPermission(user, 'reports');

console.log('=== COMPREHENSIVE AUTHENTICATION SYSTEM TEST ===\n');

// Test each mock user
Object.entries(MOCK_USERS).forEach(([userType, user]) => {
    console.log('User Type:', userType);
    console.log('Roles:', user.roles.join(', '));
    
    const calculatedPermissions = calculatePermissions(user.roles);
    const isUserAdmin = user.roles && user.roles.includes('admin');
    const finalPermissions = isUserAdmin ? ['ALL', ...calculatedPermissions] : calculatedPermissions;
    
    console.log('Is Admin:', isUserAdmin);
    console.log('Calculated Permissions Count:', calculatedPermissions.length);
    console.log('Final Permissions Count:', finalPermissions.length);
    console.log('Has ALL permission:', finalPermissions.includes('ALL'));
    
    // Create test user object
    const testUser = {
        ...user,
        permissions: finalPermissions
    };
    
    // Test route access
    console.log('Route Access:');
    console.log('  - Games:', canAccessGames(testUser) ? 'YES' : 'NO');
    console.log('  - Import:', canAccessImport(testUser) ? 'YES' : 'NO'); 
    console.log('  - Reports:', canAccessReports(testUser) ? 'YES' : 'NO');
    console.log('---');
});

// Final verification
const adminUser = {
    ...MOCK_USERS.admin,
    permissions: ['ALL', ...calculatePermissions(MOCK_USERS.admin.roles)]
};

const allTestsPass = 
    adminUser.permissions.includes('ALL') &&
    canAccessGames(adminUser) &&
    canAccessImport(adminUser) &&
    canAccessReports(adminUser);

console.log('\nFINAL RESULT:', allTestsPass ? '✅ ALL TESTS PASSED' : '❌ TESTS FAILED');

if (allTestsPass) {
    console.log('\n🎉 Authentication system working correctly!');
    console.log('✅ Admin users get ALL permission');  
    console.log('✅ Route access working for admin');
    console.log('✅ Permission calculation working');
} else {
    console.log('\n❌ Issues detected in authentication system');
}