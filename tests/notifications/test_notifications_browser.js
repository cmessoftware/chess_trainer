// Test rápido de notificaciones desde consola de Chrome
// Copiar y pegar en la consola del navegador (F12) cuando estés logueado

(async () => {
    const token = localStorage.getItem('token');

    if (!token) {
        console.error('❌ No hay token en localStorage. Debes estar logueado.');
        return;
    }

    console.log('🔑 Token encontrado:', token.substring(0, 20) + '...');

    try {
        // Intentar obtener notificaciones
        const response = await fetch('http://localhost:8000/api/features/notifications', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        console.log('📡 Status:', response.status);

        if (response.ok) {
            const data = await response.json();
            console.log('✅ Notificaciones obtenidas:', data.length);

            if (data.length > 0) {
                console.log('📋 Primera notificación:');
                console.log(data[0]);
            } else {
                console.log('⚠️ No hay notificaciones.');
                console.log('💡 Solución: Sube un PGN y presiona "Extraer Features" para generar notificaciones.');
            }
        } else {
            const error = await response.json();
            console.error('❌ Error:', error);
        }
    } catch (err) {
        console.error('💥 Exception:', err);
    }
})();

console.log('🚀 Ejecutando test de notificaciones...');
