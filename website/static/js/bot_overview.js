function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');

    const sidebarDots = document.getElementById('sidebar_dots');
    sidebarDots.classList.toggle('rotate-90');
}
