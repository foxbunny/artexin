begin transaction;

alter table content rename to tmp;

create table content
(
    id integer primary key,             -- content ID

    md5 varchar unique,                        -- md5 of the URL
    url varchar,                        -- original URL
    title varchar,                      -- page title
    archive varcher,                    -- name of archive to which content belongs
    images integer default 0,           -- number of images

    is_sponsored boolean,               -- whether content is sponsored
    is_partner boolean,                 -- whether content is from partener
    partner varchar,                    -- name of sponsor/partner

    created timestamp,                  -- creation timestamp
    updated timestamp                   -- update timestamp
);

replace into content
(id, md5, url, title, archive, images, is_sponsored, is_partner, partner,
created, updated)
select
id, md5, url, title, archive, images, is_sponsored, is_partner, partner,
created, updated
from tmp;

drop table tmp;

commit transaction;
