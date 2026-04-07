import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TagType } from '../../types/tag';
import TagSelector from '../../components/TagSelector';

describe('TagSelector', () => {
  const mockTags: TagType[] = [
    { id: '1', name: 'Python', color: 'blue', description: 'Python programming language' },
    { id: '2', name: 'JavaScript', color: 'yellow', description: 'JavaScript programming language' },
    { id: '3', name: 'TypeScript', color: 'blue', description: 'TypeScript programming language' },
  ];

  it('renders all tags', () => {
    const mockOnTagToggle = jest.fn();
    const { container } = render(
      <TagSelector 
        tags={mockTags} 
        selectedTagIds={[]} 
        onTagToggle={mockOnTagToggle} 
      />
    );
    
    expect(container).toMatchSnapshot();
  });

  it('calls onTagToggle when a tag is clicked', () => {
    const mockOnTagToggle = jest.fn();
    render(
      <TagSelector 
        tags={mockTags} 
        selectedTagIds={[]} 
        onTagToggle={mockOnTagToggle} 
      />
    );
    
    const tagButton = screen.getByText('Python');
    fireEvent.click(tagButton);
    
    expect(mockOnTagToggle).toHaveBeenCalledWith('1');
  });

  it('applies correct styling for selected tags', () => {
    const mockOnTagToggle = jest.fn();
    render(
      <TagSelector 
        tags={mockTags} 
        selectedTagIds={['1']} 
        onTagToggle={mockOnTagToggle} 
      />
    );
    
    const selectedTag = screen.getByText('Python').closest('button');
    expect(selectedTag).toHaveClass('bg-blue-500', 'text-white');
  });

  it('applies correct styling for unselected tags', () => {
    const mockOnTagToggle = jest.fn();
    render(
      <TagSelector 
        tags={mockTags} 
        selectedTagIds={[]} 
        onTagToggle={mockOnTagToggle} 
      />
    );
    
    const unselectedTag = screen.getByText('Python').closest('button');
    expect(unselectedTag).toHaveClass('bg-blue-100', 'text-blue-800');
  });
});