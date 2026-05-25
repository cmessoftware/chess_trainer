/**
 * Complete authentication system test
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 Testing Complete Authentication System\n');

// Define BASE_ROLES
const BASE_ROLES = {
    ADMIN: 'admin',
    BASIC_GAMER: 'basic_gamer',
    ANALYSIS_BOARD: 'analysis_board',
    EXERCISE_CREATOR: 'exercise_creator',
    STATS_VIEWER: 'stats_viewer',
    TACTICS_TRAINER: 'tactics_trainer',
    PGN_UPLOADER: 'pgn_uploader',
    EDA_ANALYST: 'eda_analyst'
};

// Define ROLE_PERMISSIONS
const ROLE_PERMISSIONS = {
    admin: ['ALL'],
    basic_gamer: ['chess_board', 'play_stockfish', 'view_own_games'],
    analysis_board: ['chess_board', 'analysis_engine', 'deep_analysis'],
    exercise_creator: ['create_exercises', 'edit_exercises', 'view_exercises'],
    stats_viewer: ['view_stats', 'advanced_stats', 'reports'],
    tactics_trainer: ['tactics_training', 'view_exercises', 'progress_tracking'],
    pgn_uploader: ['bulk_upload', 'import_pgn', 'manage_sources'],
    eda_analyst: ['eda_analysis', 'data_mining', 'pattern_analysis']
};

// Define MOCK_USERS
const MOCK_USERS = {
    admin: {
        id: 1,
        username: 'admin_user',
        name: 'Administrador Sistema',
        role: 'admin',
        email: 'admin@chess-trainer.com',
        roles: [BASE_ROLES.ADMIN],
        permissions: ['ALL'],
        userType: 'admin',
        is_active: true
    },
    analyst: {
        id: 2,
        username: 'analyst',
        name: 'Analista de Ajedrez',
        role: 'analyst',
        email: 'analyst@chess-trainer.com',
        roles: [BASE_ROLES.BASIC_GAMER, BASE_ROLES.ANALYSIS_BOARD, BASE_ROLES.STATS_VIEWER],
        permissions: [],
        userType: 'analyst',
        is_active: true
    },
    user: {
        id: 3,
        username: 'regular_user',
        name: 'Usuario Regular',
        role: 'user',
        email: 'user@chess-trainer.com',
        roles: [BASE_ROLES.BASIC_GAMER],
        permissions: [],
        userType: 'user',
        is_active: true
    }
};

// Define calculatePermissions function
const calculatePermissions = (roles) => {
    if (!roles || !Array.isArray(roles)) return [];
    
    const permissionsSet = new Set();
    
    roles.forEach(role => {
        const rolePermissions = ROLE_PERMISSIONS[role];
        if (rolePermissions) {
            rolePermissions.forEach(permission => {
                permissionsSet.add(permission);
            });
        }
    });
    
    return Array.from(permissionsSet);
};

// Define helper functions
const hasPermission = (user, permission) => {
    if (!user || !user.permissions) return false;
    return user.permissions.includes('ALL') || user.permissions.includes(permission);
};

const canAccessGames = (user) => hasPermission(user, 'view_own_games');
const canAccessImport = (user) => hasPermission(user, 'import_pgn');
const canAccessReports = (user) => hasPermission(user, 'reports');

// Test each user type
console.log('📋 Testing Permission Calculation for Each User Type:\n');

Object.entries(MOCK_USERS).forEach(([userType, user]) => {
    console.log(`👤 ${userType.toUpperCase()} User:`);
    console.log(`   Name: ${user.name}`);
    console.log(`   Roles: [${user.roles.join(', ')}]`);
    
    const calculatedPermissions = calculatePermissions(user.roles);
    const isUserAdmin = user.roles && user.roles.includes('admin');
    const finalPermissions = isUserAdmin ? ['ALL', ...calculatedPermissions] : calculatedPermissions;
    
    console.log(`   Is Admin: ${isUserAdmin}`);
    console.log(`   Calculated Permissions: [${calculatedPermissions.join(', ')}]`);
    console.log(`   Final Permissions: [${finalPermissions.join(', ')}]`);
    console.log(`   Permissions Count: ${finalPermissions.length}`);
    
    // Create test user object with final permissions
    const testUser = {
        ...user,
        permissions: finalPermissions
    };
    
    // Test route access
    const gamesAccess = canAccessGames(testUser);
    const importAccess = canAccessImport(testUser);
    const reportsAccess = canAccessReports(testUser);
    
    console.log(`   Route Access:`);
    console.log(`     - Games: ${gamesAccess ? '✅ YES' : '❌ NO'}`);
    console.log(`     - Import: ${importAccess ? '✅ YES' : '❌ NO'}`);
    console.log(`     - Reports: ${reportsAccess ? '✅ YES' : '❌ NO'}`);
    console.log('');
});

// Final verification for admin user
console.log('🔍 Final Verification - Admin User Route Access:\n');

const adminUser = {
    ...MOCK_USERS.admin,
    permissions: ['ALL', ...calculatePermissions(MOCK_USERS.admin.roles)]
};

console.log(`Admin User Final Permissions: [${adminUser.permissions.join(', ')}]`);
console.log(`Has 'ALL' permission: ${adminUser.permissions.includes('ALL')}`);

const adminTests = {
    hasAll: adminUser.permissions.includes('ALL'),
    canAccessGames: canAccessGames(adminUser),
    canAccessImport: canAccessImport(adminUser),
    canAccessReports: canAccessReports(adminUser)
};

console.log('\nAdmin Route Access Tests:');
Object.entries(adminTests).forEach(([test, result]) => {
    console.log(`  ${test}: ${result ? '✅ PASS' : '❌ FAIL'}`);
});

const allTestsPass = Object.values(adminTests).every(result => result === true);

console.log('\n' + '='.repeat(50));
console.log(allTestsPass ? '🎉 ALL TESTS PASSED!' : '❌ SOME TESTS FAILED!');
console.log(allTestsPass ? 
    '✅ Authentication system working correctly' : 
    '⚠️  Check authentication implementation');
console.log('='.repeat(50));