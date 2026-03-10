<!DOCTYPE html>
<html>
    <head>
        <title>Temperatuurlogger</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-sRIl4kxILFvY47J16cr9ZwB07vP4J8+LH7qKQnuqkuIAvNWLzeN8tE5YBujZqJLB" crossorigin="anonymous">
        <style>
            body{
                margin-top: 80px;
            }
            .carousel {
                min-height: 650px;
                background-color: #f0f0f0;
            }
            .carousel-item img {
                height: 600px;
                object-fit: contain;
            }
            .carousel-caption{
                color:black;
            }
        </style>
    </head>
    <body>
        <?php include 'Navbar.php' ?>
        <div class="container-fluid mt-4">
        <h2>Temperatuur Grafieken</h2>
        <div id="caroussel" class="carousel slide" data-bs-ride="carousel">
        <div class="carousel-indicators">
        <button type="button" data-bs-target="#caroussel" data-bs-slide-to="0" class="active" aria-current="true" aria-label="Slide 1"></button>
        <button type="button" data-bs-target="#caroussel" data-bs-slide-to="1" aria-label="Slide 2"></button>
        </div>
        <div class="carousel-inner">
        <div class="carousel-item active">
        <img src="Assets/DagTemperatuur.png" class="d-block w-100" alt="Dagtemperatuur">
        <div class="carousel-caption d-none d-md-block">
        <h5>Dagtemperatuur</h5>
        </div>
        </div>
        <div class="carousel-item">
        <img src="Assets/WeekTemperatuur.png" class="d-block w-100" alt="Weektemperatuur">
        <div class="carousel-caption d-none d-md-block">
        <h5>Weektemperatuur</h5>
        </div>
        </div>
        </div>
        <button class="carousel-control-prev" type="button" data-bs-target="#caroussel" data-bs-slide="prev">
        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Previous</span>
        </button>
        <button class="carousel-control-next" type="button" data-bs-target="#caroussel" data-bs-slide="next">
        <span class="carousel-control-next-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Next</span>
        </button>
        </div>
        </div>
    </body>
    <footer>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js" integrity="sha384-FKyoEForCGlyvwx9Hj09JcYn3nv7wiPVlz7YYwJrWVcXK/BmnVDxM+D2scQbITxI" crossorigin="anonymous"></script>
    </footer>
</html>
