import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-simulations',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './simulations.html',
  styleUrls: ['./simulations.scss'],
})
export class SimulationsComponent {
  environments = [
    { name: 'Urban Intersection', collisions: 2, safeRuns: 18 },
    { name: 'Highway Merge', collisions: 1, safeRuns: 19 },
    { name: 'Night Driving', collisions: 3, safeRuns: 17 },
    { name: 'Rainy Weather', collisions: 4, safeRuns: 16 },
  ];
}
