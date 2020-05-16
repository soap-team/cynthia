create table Wikis (
    wiki_id             integer,
    wiki_url            text not null,
    hub                 text not null,
    is_UCP              text not null,
    primary key (wiki_id)
);

create table Pages (
    page_id             integer,
    wiki_id             integer not null,
    title               text not null,
    namespace           text not null,
    foreign key (wiki_id) references Wikis(wiki_id),
    primary key (page_id)
);

create table User_info (
    user_id             integer,
    edit_count          integer not null,
    global_edit_count   integer not null,
    registration        text not null,
    local_groups        text not null,
    primary key (user_id)
);

create table Revisions (
    revision_id         integer,
    page_id             integer not null,
    user_id             integer not null,
    wiki_id             integer not null,
    timestamp           text not null,
    comment             text not null,
    byte_length         text not null,
    flags               text not null,
    text                text not null,
    parent              text not null,
    diff                text not null,
    namespace           text not null,
    foreign key (page_id) references Pages(page_id),
    foreign key (user_id) references User_info(user_id),
    foreign key (wiki_id) references Wikis(wiki_id),
    primary key (revision_id)
);

create table Categories (
    revision_id         integer not null,
    damaging            text,
    spam                text,
    goodfaith           text,
    foreign key (revision_id) references Revisions(revision_id),
    primary key (revision_id)
);


