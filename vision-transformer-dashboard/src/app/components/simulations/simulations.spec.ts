import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Simulations } from './simulations';

describe('Simulations', () => {
  let component: Simulations;
  let fixture: ComponentFixture<Simulations>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Simulations]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Simulations);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
