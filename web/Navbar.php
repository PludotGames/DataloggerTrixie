<nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
<div class="container-fluid">
<a class="navbar-brand" href="#">Temperatuurlogger
</a>
<button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
<span class="navbar-toggler-icon"></span>
</button>

<div class="collapse navbar-collapse" id="navbarNav">
<ul class="navbar-nav ms-auto">
<li class="nav-item">
<a class="nav-link <?= ($current_page == 'index.php') ? 'active' : '' ?>" href="index.php">Home</a>
</li>
<li class="nav-item">
<a class="nav-link <?= ($current_page == 'Dag.php') ? 'active' : '' ?>" href="Dag.php">Dag</a>
</li>
<li class="nav-item">
<a class="nav-link <?= ($current_page == 'Week.php') ? 'active': '' ?>" href="Week.php">Week</a>
</li>
<li class="nav-item">
<a class="nav-link <?= ($current_page == 'Maand.php') ? 'active': '' ?>" href="Maand.php">Maand</a>
</li>
<li class="nav-item">
<a class="nav-link <?= ($current_page == 'AllTime.php') ? 'active': '' ?>" href="AllTime.php">Al de tijd</a>
</li>
</ul>
</div>
</div>
</nav>
