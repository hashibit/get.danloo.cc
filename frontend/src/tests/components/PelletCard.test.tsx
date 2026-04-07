import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import PelletCard from '../../components/PelletCard';

describe('PelletCard', () => {
  const mockPellet = {
    id: 'pellet-1',
    title: 'Test Pellet',
    tags: [],
  };

  const mockOnView = jest.fn();
  const mockOnShare = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders pellet title correctly', () => {
    render(
      <PelletCard
        {...mockPellet}
        onView={mockOnView}
        onShare={mockOnShare}
      />
    );

    expect(screen.getByText('Test Pellet')).toBeInTheDocument();
  });

  it('renders with tags', () => {
    const pelletWithTags = {
      ...mockPellet,
      tags: [{ id: 'gold', name: '金丹', color: 'yellow', description: 'High quality pellets with golden content' }],
    };

    render(
      <PelletCard
        {...pelletWithTags}
        onView={mockOnView}
        onShare={mockOnShare}
      />
    );

    expect(screen.getByText('金丹')).toBeInTheDocument();
  });

  it('renders default tag when no tags provided', () => {
    render(
      <PelletCard
        {...mockPellet}
        onView={mockOnView}
        onShare={mockOnShare}
      />
    );

    expect(screen.getByText('普通丹')).toBeInTheDocument();
  });

  it('calls onView when view button is clicked', () => {
    render(
      <PelletCard
        {...mockPellet}
        onView={mockOnView}
        onShare={mockOnShare}
      />
    );

    const viewButton = screen.getByText('View');
    fireEvent.click(viewButton);

    expect(mockOnView).toHaveBeenCalledWith('pellet-1');
  });

  it('calls onShare when share button is clicked', () => {
    render(
      <PelletCard
        {...mockPellet}
        onView={mockOnView}
        onShare={mockOnShare}
      />
    );

    const shareButton = screen.getByText('Share');
    fireEvent.click(shareButton);

    expect(mockOnShare).toHaveBeenCalledWith('pellet-1');
  });
});