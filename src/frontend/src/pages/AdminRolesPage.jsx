import React, { useState, useEffect } from 'react';
import {
    Grid,
    Paper,
    Typography,
    Checkbox,
    FormControlLabel,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Button,
    Box,
    Card,
    CardContent,
    Chip,
    Alert,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    MenuItem,
    FormControl,
    InputLabel,
    Select,
    OutlinedInput
} from '@mui/material';
import {
    Person,
    Security,
    Assignment,
    Add as AddIcon,
    Edit as EditIcon,
    Save as SaveIcon,
    Cancel as CancelIcon
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';

const AdminRolesPage = () => {
    const { user, token } = useAuth();
    const [users, setUsers] = useState([]);
    const [rolesMatrix, setRolesMatrix] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [editingUser, setEditingUser] = useState(null);
    const [selectedRoles, setSelectedRoles] = useState([]);
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [newUser, setNewUser] = useState({
        username: '',
        email: '',
        password: '',
        roles: []
    });

    // Color mapping for roles
    const roleColors = {
        admin: 'error',
        basic_gamer: 'primary',
        analysis_board: 'secondary',
        exercise_creator: 'success',
        stats_viewer: 'info',
        tactics_trainer: 'warning',
        pgn_uploader: 'default',
        eda_analyst: 'error'
    };

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);

            // Fetch users and roles matrix in parallel
            const [usersResponse, matrixResponse] = await Promise.all([
                fetch('/api/auth/users', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }),
                fetch('/api/auth/roles/matrix', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                })
            ]);

            if (!usersResponse.ok || !matrixResponse.ok) {
                throw new Error('Error fetching data');
            }

            const usersData = await usersResponse.json();
            const matrixData = await matrixResponse.json();

            setUsers(usersData);
            setRolesMatrix(matrixData);
            setError(null);
        } catch (err) {
            console.error('Error fetching data:', err);
            setError('Error al cargar los datos: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRoleToggle = (userId, roleName) => {
        if (editingUser === userId) {
            const updatedRoles = selectedRoles.includes(roleName)
                ? selectedRoles.filter(r => r !== roleName)
                : [...selectedRoles, roleName];
            setSelectedRoles(updatedRoles);
        }
    };

    const startEdit = (userId) => {
        const user = users.find(u => u.id === userId);
        setEditingUser(userId);
        setSelectedRoles(user.roles || []);
    };

    const cancelEdit = () => {
        setEditingUser(null);
        setSelectedRoles([]);
    };

    const saveRoles = async (userId) => {
        try {
            const response = await fetch(`/api/auth/users/${userId}/roles`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(selectedRoles)
            });

            if (!response.ok) {
                throw new Error('Error updating roles');
            }

            const updatedUser = await response.json();

            // Update local state
            setUsers(users.map(u => u.id === userId ? updatedUser : u));
            setEditingUser(null);
            setSelectedRoles([]);

        } catch (err) {
            console.error('Error saving roles:', err);
            setError('Error al guardar los roles: ' + err.message);
        }
    };

    const handleCreateUser = async () => {
        try {
            const response = await fetch('/api/auth/users', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newUser)
            });

            if (!response.ok) {
                throw new Error('Error creating user');
            }

            const createdUser = await response.json();
            setUsers([...users, createdUser]);
            setShowCreateDialog(false);
            setNewUser({
                username: '',
                email: '',
                password: '',
                roles: []
            });
        } catch (err) {
            console.error('Error creating user:', err);
            setError('Error al crear usuario: ' + err.message);
        }
    };

    const applyRoleCombination = (userId, combination) => {
        if (!rolesMatrix?.role_combinations[combination]) return;

        if (editingUser === userId) {
            setSelectedRoles([...rolesMatrix.role_combinations[combination]]);
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <Typography>Cargando...</Typography>
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error" sx={{ m: 2 }}>
                {error}
            </Alert>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Security />
                Administración de Roles
            </Typography>

            {/* Role Combinations Quick Actions */}
            <Card sx={{ mb: 3 }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Assignment />
                        Combinaciones Predefinidas
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {rolesMatrix?.role_combinations && Object.entries(rolesMatrix.role_combinations).map(([name, roles]) => (
                            <Chip
                                key={name}
                                label={`${name} (${roles.length} roles)`}
                                variant="outlined"
                                color="primary"
                                size="small"
                                sx={{ cursor: 'pointer' }}
                                onClick={() => editingUser && applyRoleCombination(editingUser, name)}
                            />
                        ))}
                    </Box>
                </CardContent>
            </Card>

            {/* Create User Button */}
            <Box sx={{ mb: 2 }}>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setShowCreateDialog(true)}
                    color="primary"
                >
                    Crear Usuario
                </Button>
            </Box>

            {/* Users and Roles Matrix */}
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell><strong>Usuario</strong></TableCell>
                            <TableCell><strong>Email</strong></TableCell>
                            {rolesMatrix?.available_roles.map(role => (
                                <TableCell key={role.name} align="center">
                                    <Box sx={{ textAlign: 'center' }}>
                                        <Typography variant="caption" display="block">
                                            {role.name.replace(/_/g, ' ').toUpperCase()}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary" display="block">
                                            {role.permissions.length} permisos
                                        </Typography>
                                    </Box>
                                </TableCell>
                            ))}
                            <TableCell><strong>Acciones</strong></TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {users.map(user => (
                            <TableRow key={user.id} sx={{ '&:nth-of-type(odd)': { backgroundColor: 'action.hover' } }}>
                                <TableCell>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Person />
                                        <Box>
                                            <Typography variant="body2" fontWeight="bold">
                                                {user.username}
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                ID: {user.id}
                                            </Typography>
                                        </Box>
                                    </Box>
                                </TableCell>
                                <TableCell>
                                    <Typography variant="body2">
                                        {user.email}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        Activo: {user.is_active ? 'Sí' : 'No'}
                                    </Typography>
                                </TableCell>
                                {rolesMatrix?.available_roles.map(role => (
                                    <TableCell key={role.name} align="center">
                                        <Checkbox
                                            checked={
                                                editingUser === user.id
                                                    ? selectedRoles.includes(role.name)
                                                    : (user.roles || []).includes(role.name)
                                            }
                                            onChange={() => handleRoleToggle(user.id, role.name)}
                                            disabled={editingUser !== user.id}
                                            color={roleColors[role.name] || 'primary'}
                                            sx={{
                                                '& .MuiSvgIcon-root': { fontSize: 28 },
                                                transform: (user.roles || []).includes(role.name) ? 'scale(1.1)' : 'scale(1)'
                                            }}
                                        />
                                    </TableCell>
                                ))}
                                <TableCell>
                                    <Box sx={{ display: 'flex', gap: 1 }}>
                                        {editingUser === user.id ? (
                                            <>
                                                <Button
                                                    size="small"
                                                    variant="contained"
                                                    color="success"
                                                    startIcon={<SaveIcon />}
                                                    onClick={() => saveRoles(user.id)}
                                                >
                                                    Guardar
                                                </Button>
                                                <Button
                                                    size="small"
                                                    variant="outlined"
                                                    startIcon={<CancelIcon />}
                                                    onClick={cancelEdit}
                                                >
                                                    Cancelar
                                                </Button>
                                            </>
                                        ) : (
                                            <Button
                                                size="small"
                                                variant="outlined"
                                                startIcon={<EditIcon />}
                                                onClick={() => startEdit(user.id)}
                                            >
                                                Editar
                                            </Button>
                                        )}
                                    </Box>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* User Roles Summary */}
            <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Resumen de Roles por Usuario
                </Typography>
                <Grid container spacing={2}>
                    {users.map(user => (
                        <Grid item xs={12} md={6} lg={4} key={user.id}>
                            <Card>
                                <CardContent>
                                    <Typography variant="h6" gutterBottom>
                                        {user.username}
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                        {(user.roles || []).map(role => (
                                            <Chip
                                                key={role}
                                                label={role.replace(/_/g, ' ').toUpperCase()}
                                                size="small"
                                                color={roleColors[role] || 'default'}
                                            />
                                        ))}
                                        {(!user.roles || user.roles.length === 0) && (
                                            <Typography variant="caption" color="text.secondary">
                                                Sin roles asignados
                                            </Typography>
                                        )}
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            </Box>

            {/* Create User Dialog */}
            <Dialog open={showCreateDialog} onClose={() => setShowCreateDialog(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Crear Nuevo Usuario</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
                        <TextField
                            label="Nombre de usuario"
                            value={newUser.username}
                            onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                            fullWidth
                            required
                        />
                        <TextField
                            label="Email"
                            type="email"
                            value={newUser.email}
                            onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                            fullWidth
                            required
                        />
                        <TextField
                            label="Contraseña"
                            type="password"
                            value={newUser.password}
                            onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                            fullWidth
                            required
                        />
                        <FormControl fullWidth>
                            <InputLabel>Roles</InputLabel>
                            <Select
                                multiple
                                value={newUser.roles}
                                onChange={(e) => setNewUser({ ...newUser, roles: e.target.value })}
                                input={<OutlinedInput label="Roles" />}
                                renderValue={(selected) => (
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {selected.map((value) => (
                                            <Chip key={value} label={value.replace(/_/g, ' ')} size="small" />
                                        ))}
                                    </Box>
                                )}
                            >
                                {rolesMatrix?.available_roles.map(role => (
                                    <MenuItem key={role.name} value={role.name}>
                                        {role.name.replace(/_/g, ' ').toUpperCase()}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setShowCreateDialog(false)}>
                        Cancelar
                    </Button>
                    <Button
                        onClick={handleCreateUser}
                        variant="contained"
                        disabled={!newUser.username || !newUser.email || !newUser.password}
                    >
                        Crear Usuario
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default AdminRolesPage;