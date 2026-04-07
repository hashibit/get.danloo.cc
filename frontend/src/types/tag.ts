export interface TagType {
  id: string;
  name: string;
  color: string;
  description: string;
}

export interface PelletTag {
  pelletId: string;
  tagId: string;
}

export interface PelletWithTags {
  id: string;
  title: string;
  viewCount: number;
  tags: TagType[];
}